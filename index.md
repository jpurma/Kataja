---
layout: page
title: Visualising biolinguistics
---

{% include image name="purplebanner.jpg" %}


Kataja is free and open software for visualising hypothetical syntactic structures in minimalist and biolinguistic frameworks. Most of the current models in generative theory assume few basic operations cyclically applied and these can create quite complex structures. Kataja aims to help in manipulating and evaluating these, and to make visible the current syntactic theory.  

## Drawing

Kataja lets you draw trees quickly and in free order. Kataja drawing interface enforces binary trees, but it can be fed with unary and n-branching trees. Nodes can be edited in place and new siblings can be added with a single click on "sprouts" appearing from the node. 

{% include image name="new.png" width="40%" %}

In addition to constituent nodes there are also features: smaller things that attract, repel and identify constituents, depending on a theory. These can be added to any node, and features can be shared by many constituents. 

Kataja is especially strong with multidominated structures: creating these structures is matter of dragging nodes under new parents and node being in two place at once can be visualised easily with Kataja's animated movement. Best of all, Kataja trees can be exported with single click as publication quality cropped, resolution independent PDF drawings or PNG images: 

{% include image name="beta.png" width="60%" caption="Here the leftmost β is dominated by both α and β" %}

There is no reason to believe in a single best visual presentation style for syntactic structures, whatever those might be. Kataja has 10 visualisation algorithms to try for each structure and switching between them is as simple as pressing 1... or 9. 

## Presenting

Kataja can be used in presentations or lectures, live in location, or streamed or recorded from your desktop. 

Each Kataja file is a set of 'slides', independent trees or groups of them. Everything done with the trees creates a visual response or animation, to help the audience to follow what has happened. Kataja even has a facecam widget to ease setting up recording or streaming.

{% include image name="facecam.jpg" caption="Show and tell with Kataja and a nonsensical structure" %}

Kataja is free and for everyone: the audience can have exactly the same tool as the lecturer and they can look at the examples own their own. Kataja should be both the entry level and the professional tool for figuring out the computational primitives of language.

## Experimenting

Kataja has a plugin system for developing and running syntactic models written in Python3, as complex as they get. In these cases Kataja is a visualisation framework and a utility provider: plugin sends derivation steps, or intermediate states and Kataja provides means to browse, visualise and debug them.   

<figure>
<center>
<iframe width="480" height="270" src="https://www.youtube.com/embed/wWPfta0fXo0?rel=0" frameborder="0" allowfullscreen></iframe>
<figcaption>Problems of Projection -inspired model building two example sentences</figcaption>
</center>
</figure>

Kataja provides a simple base implementation for constituents and operations such as merge. Syntax modeler can build on them, modify them or replace them.  

[›Download](/download)

