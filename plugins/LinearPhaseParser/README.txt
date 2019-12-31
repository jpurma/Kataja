
LinearPhaseParser
=================

This plugin expects the source code of Brattico's LinearPhaseParser (https://github.com/pajubrat/parser-grammar)
to be available for plugin. The default assumption is to reside next to Kataja's source folder, but this location can be
changed by modifying setup.py. This plugin works as a wrapper around the LinearPhaseParser, inheriting and overwriting
its main parse function so that the parser can export its derivation states.

