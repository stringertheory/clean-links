# Clean Links

A python library for cleaning up URLs.

---

<style>
  div.nowrap code {
    white-space : pre-wrap !important;
    word-break: break-all;
  }
  span.lank {
    text-decoration: underline;
    text-decoration-style: dotted;
    text-underline-offset: 0.33em;
	font-family: "Chivo Mono", monospace;
	letter-spacing: -0.05em;
  }
</style>

Say _@Alicia_ posts a link to <span class="lank">https://bit.ly/dirtylank</span> and _@Barry_
posts a link to <span class="lank">https://trib.al/5m7fAg3</span>. Did _@Alicia_ and _@Barry_
link to the same thing?

When you're using a browser you can click on them and find out, but if
you are making tools that try to see when people shared the same link.

**The main purpose of this library is to try to answer that question:
are two links pointing the same place.**

---

Install using pip:

```shell
$ pip install clean_links
```

Then get started by unshortening the link that _@Alicia_ posted:

<div class="nowrap">
```pycon
>>> from clean_links import unshorten_url
>>> alicia = unshorten_url("https://bit.ly/dirtylank")
>>> alicia["resolved"]
'https://www.bloomberg.com/news/articles/2024-01-24/cryptocurrency-ai-electricity-demand-seen-doubling-in-three-years?cmpid%3D=socialflow-tech&utm_content=tech&utm_medium=social&utm_campaign=socialflow-organic&utm_source=mastodon'
```
</div>

It goes to a news article at Bloomberg. The link includes a bunch of
stuff at the end used for tracking (`utm_source`, etc) that probably
has to do with where _@Alicia_ saw the link.

How about _@Barry_'s link?

<div class="nowrap">
```pycon
>>> from clean_links import unshorten_url
>>> barry = unshorten_url("https://trib.al/5m7fAg3")
>>> barry["resolved"]
'https://www.bloomberg.com/news/articles/2024-01-24/cryptocurrency-ai-electricity-demand-seen-doubling-in-three-years?cmpid%3D=socialflow-twitter-tech&utm_content=tech&utm_medium=social&utm_campaign=socialflow-organic&utm_source=twitter'
```
</div>

It does go to the same page! But it has different tracking stuff at
the end so comparing the URLs won't tell us they're the same:

```pycon
>>> alicia == barry
False
```

The `clean_url` function can help. It uses the [latest
rules](https://github.com/ClearURLs/Rules) from the
[ClearURLs](https://docs.clearurls.xyz/) web extension to remove the
unneccesary stuff from the links:

<div class="nowrap">
```pycon
>>> from clean_links import clean_url
>>> a_cleaned = clean_url(alicia["resolved"])
>>> b_cleaned = clean_url(barry["resolved"])
>>> a_cleaned
'https://www.bloomberg.com/news/articles/2024-01-24/cryptocurrency-ai-electricity-demand-seen-doubling-in-three-years'
>>> a_cleaned == b_cleaned
True
```
</div>

So after unshortening and cleaning, we can see the links that
_@Alicia_ and _@Barry_ posted were to the same article. Maybe we
should read it! The combination of unshortening and cleaning is useful
enough there's a single function, `normalize_url`, to do both.

```pycon
>>> from clean_links import normalize_url
>>> a_normed = normalize_url("https://bit.ly/dirtylank")
>>> b_normed = normalize_url("https://trib.al/5m7fAg3")
>>> a_normed == b_normed
True
```

## what it does

Lorem ipsum dolor sit amet, (1) consectetur adipiscing elit.
{ .annotate }

1.  :man_raising_hand: I'm an annotation! I can contain `code`, **formatted
    text**, images, ... basically anything that can be expressed in Markdown.

Welcome to the silly jungle. We have fun and games. Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.

![Image title](https://dummyimage.com/600x400/){width=40%, align=left}

Welcome to the silly jungle. We have fun and games. Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Test again

Welcome to the silly jungle. We have fun and games. Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Welcome to the silly jungle. We have fun and games.
Test again

!!! note

    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod
    nulla. Curabitur feugiat, tortor non consequat finibus, justo purus auctor
    massa, nec semper lorem quam in massa.

## what it don't do

Booga booga
