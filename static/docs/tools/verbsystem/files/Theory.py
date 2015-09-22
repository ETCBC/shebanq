# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from IPython.display import display, HTML

display(HTML(data="""
<style>

div#notebook {
	background-color:LightYellow;
}

div.input_area {
	background-color:LemonChiffon;
}

h1, h2, h3, h4 {
	color:Gold;
}

div.text_cell_render {
	color:DarkBlue;
}

table.presentation, table.verbs, table.patterns, table.verbal_patterns {
    margin-left: auto;
    margin-right: auto;
}

table.presentation, table.presentation tr, table.presentation th, table.presentation td {
    border-style:hidden;
    color: Maroon;
}

table.verbs, table.verbs tr, table.verbs th, table.verbs td {
    border-style: hidden;
    color: Maroon;
	text-align: center;
}

table.patterns, table.patterns tr, table.patterns th, table.patterns td {
    border-style:hidden;
    color: Maroon;
    font-size: small;
}

table.verbal_patterns, table.verbal_patterns tr, table.verbal_patterns th, table.verbal_patterns td {
    border-style:hidden;
    color: Maroon;
}

table.presentation th, table.presentation td, table.patterns th, table.patterns td {
    padding:0px 10px 0px 0px;
}

table.verbs td {
    padding:5px 10px 5px 10px;
}

table.verbs div.rotation {
	display:block;
	-webkit-transform: rotate(-90deg);
	-moz-transform: rotate(-90deg);
	filter: progid:DXImageTransform.Microsoft.BasicImage(rotation=3);
}

table.verbs td.background {
	background-color: LightCyan;
	color: DarkBlue;
	font-weight: bold;
	font-style: italic;
}

table.verbs td.foreground {
	background-color: MistyRose;
	color: DarkRed;
	font-weight: bold;
	font-style: italic;
}

table.verbal_patterns td {
    border-left-style:dotted;
	border-width-left:thin;
    border-right-style:dotted;
	border-width-right:thin;
}

table.verbs td.dimension {
    text-align:center;
    text-decoration:underline;
}

table.verbs td.form {
    font-style:italic;
    font-weight:bold;
    color:Maroon;
}

table.patterns td.head {
    text-decoration:underline;
}

table.presentation th {
    text-align:center;
}

span.hebrew, table.presentation td.hebrew {
    text-align:right;
    font-family:SBL Hebrew;
}

table.presentation td.outer {
    vertical-align:top;
}

p.note {
    font-size:small;
    font-style:italic;
}

div.button {
	max-width:15%;
	margin:auto;
}

</style>
"""))

# <codecell>


