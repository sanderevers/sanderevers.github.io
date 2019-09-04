---
title: Finding sets in the card game SET
mathjax: false
---
[SET](https://en.wikipedia.org/wiki/Set_(card_game)) is a card game of speedy pattern recognition.
Twelve cards with different symbols are dealt openly on the table, and all players simultaneously try to
find a **set** among these cards: a three-card combination that has to satisfy certain rules.
Some time ago I wrote a Python program that finds _all sets_ on the table, and explores some optimizations.

<!--more-->

> NOTE: this appeared earlier as a [recipe](http://code.activestate.com/recipes/578508-finding-sets-in-the-card-game-set/)
> in the ActiveState Python Cookbook, which is not maintained anymore. I've updated the code to Python 3 here,
> and elaborated the text.

<!--```python
{% include findingsets.py %}
```-->
<!--Look at [line 57](#file-findingsets-py-L57).-->

Here's an example of three SET cards:

<img src="/assets/img/62r.png" style="width: 100px; height: 154px; padding: 12px">
<img src="/assets/img/65r.png" style="width: 100px; height: 154px; padding: 12px">
<img src="/assets/img/77r.png" style="width: 100px; height: 154px; padding: 12px">

Each card has four attributes (or features), which can take three possible values:
- number of symbols (one/two/three)
- symbol shape (squiggle/diamond/oval)
- symbol color (red/purple/green)
- symbol shading (solid/striped/outlined)

In Python, I'll represent a card using a 4-tuple of integers (each 0/1/2). For example, the leftmost card
consists of two squiggles, green and outlined, so it's represented as `Card(1,0,2,2)`. 

Three cards form a **set** if for _each_ attribute, all three cards _either_ have the same value,
_or_ the three different values. Let's check that the combination shown above is a set:

        shading ____________
          color _________   |
          shape ______   |  |
         number ___   |  |  |
                   |  |  |  |
    first card:   (1, 0, 2, 2)
    second card:  (1, 1, 0, 2)
    third card:   (1, 2, 1, 2)
                   |  |  |  L__ all the same
                   |  |  L_____ all different
                   |  L________ all different
                   L___________ all the same

And here's a combination which is _not_ a set:

<img src="/assets/img/31r.png" style="width: 100px; height: 154px; padding: 12px">
<img src="/assets/img/68r.png" style="width: 100px; height: 154px; padding: 12px">
<img src="/assets/img/23r.png" style="width: 100px; height: 154px; padding: 12px">

        shading ____________
          color _________   |
          shape ______   |  |
         number ___   |  |  |
                   |  |  |  |
    first card:   (0, 0, 1, 1)
    second card:  (1, 1, 1, 2)
    third card:   (1, 2, 1, 0)
                   |  |  |  L__ all different
                   |  |  L_____ all the same
                   |  L________ all different
                   L___________ WRONG!

The attribute _number_ fails the test here.

## Representation

Around the 4-tuple I first define a small class `Card` and a method that lets me do 
`card0.isset(card1,card2)` to check whether `card0`, `card1` and `card2` form a set.

```python
class Card:
    
    def __init__(self,*attrs):
        # a card is a simple 4-tuple of attributes
        # each attr is supposed to be either 0, 1 or 2
        self.attrs = attrs
    
    # most readable way to express what a SET is
    def isset(self,card1,card2):
        def allsame(v0,v1,v2):       # checks one attribute
            return v0==v1 and v1==v2
        def alldifferent(v0,v1,v2):  # checks one attribute
            return len({v0,v1,v2})==3
        return all(allsame(v0,v1,v2) or alldifferent(v0,v1,v2)
                   for (v0,v1,v2)
                   in zip(self.attrs,card1.attrs,card2.attrs))

    # all 81 possible cards
    @staticmethod
    def allcards():
        return [ Card(att0,att1,att2,att3)
                   for att0 in (0,1,2)
                   for att1 in (0,1,2) 
                   for att2 in (0,1,2)
                   for att3 in (0,1,2)
               ]
```

I like how Python lets me write `isset` almost literally like the above definition of a set.
The only tricky thing you need to know is that [zip](https://docs.python.org/3/library/functions.html#zip)
transforms the three (per-card) lists of 4 attribute values
into four (per-attribute) lists of 3 card values.

> Aside: `allsame(v0,v1,v2) or alldifferent(v0,v1,v2)` could be replaced with
> `len({v0,v1,v2})!=2` for a shorter, but less readable, definition. 
  
The obvious way to find all sets in a table of 12 cards is to check every 3-card combinations using a three-level
nested loop. Let's define a table of random cards and a method that finds the sets using this
"generate and test" approach:

```python
import random

class Table:

    # a random table of n different cards
    def __init__(self,n=12):
        self.cards = random.sample(Card.allcards(),n)
    
    def findsets_gnt(self):     # generate and test
        found = []
        for i,ci in enumerate(self.cards):
            for j,cj in enumerate(self.cards[i+1:],i+1):
                for k,ck in enumerate(self.cards[j+1:],j+1):
                    if ci.isset(cj,ck):
                        found.append((ci,cj,ck))
        return found
```
 
Not every level needs to loop over all the cards: this would visit each 3-card
combination 6 separate times (and what's worse, investigate combinations that include the same card more
than once, giving wrong results).

Instead, the loops are constructed such that for each 3-card combination, the first card (in table order)
is represented by the outer loop variables (`i` for the position and `ci` for the card itself),
the second by the middle loop variables `j`/`cj`, and the third by the inner loop variables `k`/`ck`.
Lots of ❤ here for the thoughtful second argument in the standard lib
[enumerate](https://docs.python.org/3/library/functions.html#enumerate) function, which lets
you start the enumeration at any chosen number.
Together, the loops check each combination exactly once; when it is a set,
it is appended to the list of `found` sets.

## Optimizations

Although the above code solves the problem (and probably fast enough for all realistic uses),
I explored some optimizations just because I like that sort of thing; see the
[full code](#file-findingsets-py) below for the
optimized versions of `findsets`.
A first optimization is to rewrite the `isset` test. As mentioned I could use `len({v0,v1,v2})!=2`
for each attribute, but there's another alternative, with only simple integer operations: `(v0+v1+v2)%3==0`.
I applied this in
`Card.isset_mod()`[[code]](#file-findingsets-py-L84) and
`Table.findsets_gnt_mod()`[[code]](#file-findingsets-py-L22).

> `%3` yields the remainder after integer division by 3 

The second optimization step is to exploit the fact that each combination of two cards `(card0,card1)`
forms a set with _one unique other card_. This `card2` can be constructed by setting
`card2.attrs[i] = (-card0.attrs[i]-card1.attrs[i])%3`
for all `i`, as implemented in `Card.thirdcard_simple()`[[code]](#file-findingsets-py-L89).

There are faster ways for checking whether this card is on the table than by looping over the remaining cards.
In `Table.findsets_simple()`[[code]](#file-findingsets-py-L31), I put all the table cards in a dictionary `have`;
a dictionary lookup is performed using
the card's hash value instead of looping over the dictionary items.
In addition, we need to check whether the third card
is behind the other two cards in table order, otherwise sets are doubly counted---to be able to do this,
the dictionary maps each card to its position on the table.

In the final optimization, I represent the 4 attributes in one integer, with 2 bits per attribute:

    # values of each attribute are encoded like this
    0 -> 00
    1 -> 01
    2 -> 10

    # example encoding for a whole card:
    (1,0,2,1) -> 01 00 10 01   # so Card(1,0,2,1).bits==73

The purpose of this is to construct the third card by applying a single function to all 4
attributes at the same time, using 
[bitwise operators](https://wiki.python.org/moin/BitwiseOperators).
This function must be one that, given two values `x` and `y` in the two-bit representation,
calculates `(-x-y)%3` in this two-bit representation, and that can only use these bitwise operators.
I won't go into details but I found it with a little help from
[Karnaugh maps](https://en.wikipedia.org/wiki/Karnaugh_map); the result is
`Card.thirdcard_fast()`[[code]](#file-findingsets-py-L93).

This 8-bit representation of cards provides another optimization opportunity.
Instead of keeping track of which cards are on the table using a _dictionary_, I store the same
information in a 256-element _list_ (also called `have`): for all cards on the table, I set
`have[card.bits]=position` (and otherwise `have[card.bits]=-1`). Indexing the list to check whether
a card is on the table is probably faster than the corresponding dictionary lookup.

## Full code

{% gist cc158b28b82e6f90498b4a33ba9a6333 findingsets.py %}
