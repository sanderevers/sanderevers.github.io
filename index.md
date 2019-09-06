{::options parse_block_html="true" /}
<div style="font-style:italic">

### [---about this blog](about.html)

This is a place where I collect some (links to) articles,
mostly about software, that I've written myself. [Read more...](about.html).  
</div> 

{% for post in site.posts %}
### [{{post.title}}]({{post.url}})

{{ post.excerpt }} [_Read more..._]({{post.url}})

{% endfor %}
