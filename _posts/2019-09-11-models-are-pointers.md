---
title: Models are pointers
---

> This was written a couple of years ago for the Topicus Onderwijs blog,
> when I was working with [Apache Wicket](https://wicket.apache.org/)
> on a daily basis.

When I was first introduced to Wicket application code, I was frequently confused
by the (omni)presence of Models. If a page or component had to interact with
a database entity, it would often (though not always) be wrapped in a Model.
For example, a Page would receive a "plain" entity in its constructor, then "produce" a Model for the entity by itself, and store it
somewhere in the page state. It was a small mystery to me what the added value was in having a Model instead of the entity itself.

<!--more-->
Of course, I soon learnt that these Models were necessary in order to serialize the page between requests.
The database entities in the page state cannot trivially be serialized, because of their relations to a potentially
vast network of other entities, all prone to change between HTTP requests. Therefore, instead of the entity itself,
the Model retains its database ID, and when the page is revived, the Model will ask Hibernate for an up-to-date version
of the entity and its relations.

Thus, the notion that _models are for serialization_ took hold in my mind, where it would stay untouched for a long time.
It took away most of the confusion, but not all; I still sometimes found myself
copying patterns with Models I saw elsewhere, instead of understanding
what the situation really demanded.

Then, we started building REST client applications in Wicket. These applications
don't have a connection with the database, but talk to a REST backend using
data transfer objects, which represent a small fragment of the database (usually one entity
with its fields and sometimes a few "subordinate" entities). The typical use in
a Wicket page is like this:

```java
class PersonPage extends Page {

    @Inject
    PersonRestClient personClient;

    private IModel<RPerson> personModel;

    public PersonPage(long personID)
    {
        // HTTP GET request to /person/{personID},
        // fetches a data transfer object RPerson
        RPerson person = personClient.get(personID);

        personModel = Model.of(person);
        add(new PersonHeaderPanel("header",personModel));
        add(new PersonDetailsPanel("details",personModel));
    }
}
```

Surprise, surprise. In this code, `personModel` has no function for serialization whatsoever.
It does not contain a database entity `Person`, but a data transfer object `RPerson`,
which can be serialized just fine (that's sort of its purpose). If we
would leave out the Model and just store the `RPerson` in the page state, the page
would render and serialize without any problems. So, what is the purpose of having a Model here?

In fact, the answer had been staring me in the eye since the first time I saw the `IModel` interface: _models are essentially pointers_.

## Pointers

Pointers, for those born in more recent times, are a feature of certain programming languages
like C and C++ (but not of Java; its lack of pointers is one reason why it became so popular).
They are variables that, instead of containing a simple value, contain the
_memory address_ of another variable. In C, they look like this:

```c
void setTo42(int* p) {
    *p = 42;    // update the value of the variable that p points to
}

int main() {
    int a = 99;
    int* pointer_to_a = a&;        // assign a's address to pointer_to_a
    printf("%d\n",*pointer_to_a);  // prints 99
    setTo42(pointer_to_a);
    printf("%d\n",a);              // prints 42
}
```

In the `main` function, `pointer_to_a` is declared as an `int*` (pointer to `int`) and is pointed
at `a` (that is, ``a``'s address, denoted by `a&`, is stored in `pointer_to_a`).
In the following `printf` statement, we _dereference_ the pointer using the
`*pointer_to_a` syntax to get at the variable `a` again, and print its value.
Next, `pointer_to_a` is passed to function `setTo42`. That is, its _value_ (``a``'s address) is copied into ``setTo42``'s local variable `p`.
There, `p` is dereferenced, and the integer 42 is written at the memory address. After `setTo42` returns, `main` finds that
the value of its own **local** variable `a` has been changed to 42, with total disregard for the scope barriers that make high-level programming sane.

Without pointers, this is impossible. Function call semantics in C are "pass-by-value": whenever a function is called, its actual argument is
evaluated and this value is copied to a variable local to this function. This is also true for Java. If you pass an `int` variable into a
function, its value is always still the same after the call returns. If you pass an `Integer` variable into a function (even though under the hood Java
is actually passing a reference to an `Integer` object), its value is always still the same after the call returns. If you pass a `Person` variable
into a function, the `Person` in the variable always still has the same object identity after the call returns; the most the function can do is change some property like its first name.

However, we can simulate the use of pointers by wrapping the `Person` object in a Model. Then, when we pass the Model into a function, this function
cannot change the object identity of the Model that the calling function or object holds in some variable or field, but it _can_ change the contents
of the Model, using its `setObject` method. Thus, we can recognize pointer operations in the two methods of the `IModel` interface:

```java
o1 = m.getObject();  // o1 = *m;
m.setObject(o2);     // *m = o2;
```

We use these pointers to share state between two or more Wicket components.

## Models are Wicket's take on shared state

Shared state is one of the two fundamental ways of communicating between systems,
processes or objects. The other one is _message passing_, which is like function calls
between code living in different processes. Or actually, maybe it's better to think of it the other way around:
functions (or: objects) have been invented to simulate different processes with their own memory space, where there's actually
only one process with one memory space.

Anyway, _with the focus on Models, Wicket has adopted the shared state metaphor for
communication in its application code._ Metaphor, because underneath there is a lot of "message passing"
going on in the Wicket framework code itself; but the application programmer (ideally) does not have to
be aware of this.
Let's see how this works in practice:

```java
class PersonPage extends Page {

    @Inject
    PersonRestClient personClient;

    private IModel<RPerson> personModel;

    public PeoplePage()
    {
        // fetch the first 20 people
        List<RPerson> people = personRestClient.list(0,20);
        
        personModel = Model.of(people.get(0));

        OmschrijfbaarDropDownChoice<RPerson> choice =
            new OmschrijfbaarDropDownChoice<>("choice",personModel,people);
        PersonDetailsPanel details =
            new PersonDetailsPanel("details",personModel);
        choice.connectListForAjaxRefresh(details);

        add(choice);
        add(details);
    }
}
```

This creates a page with two components.
The first is a drop-down list of people (`OmschrijfbaarDropDownChoice` is a generic drop-down list for objects implementing
the `Omschrijfbaar` interface, consisting of a `toString`-like method).
The second is a panel showing details of the person selected in the drop-down list.
When the user selects a new person in the list, the browser fires an Ajax request, which is handled by `OmschrijfbaarDropDownChoice` in the following way:

* It updates its model, which is `personModel`.
* It adds the `PersonDetailsPanel` to the `AjaxRequestTarget` (we have made it aware of this dependent component using `connectListForAjaxRefresh`).
* This causes the `PersonDetailsPanel` to re-render itself; because its model has changed, it contains new person details.
* These changes are relayed to the browser in the Ajax response.

The important thing here is that we made the two components communicate solely by configuring them with a shared model. (Well, almost. There's the
`connectListForAjaxRefresh` which is a small flaw. If the drop-down component would perform a complete page fetch instead of an Ajax call,
we wouldn't even need it.)
The alternative to using Models would be something like defining an `update(RPerson newPerson)` function in `PersonDetailsPanel`, and calling this
function in the (overridden) `onUpdate` handler of the drop-down list.
Although this kind of message passing between components is not uncommon in our Wicket application code, I found that
if I go along with the shared state metaphor and do most communication through models, it becomes much easier
to define reusable components, and the code in general also gets easier to understand, maintain and refactor.

## Final thoughts

When it dawned on me that Wicket components are designed to communicate through shared state, the pieces really clicked
together for me. In hindsight, this architectural choice is so central to how Wicket works, that it surprises me that I haven't
seen it spelled out somewhere before, which is why I've written it down here. I hope it has helped you as much as it would
have helped me.

There's just one problem now: if shared state is frowned upon in software engineering because it "disregards the sanitary barriers between processes",
why does it work so well in designing loosely coupled Wicket components?
