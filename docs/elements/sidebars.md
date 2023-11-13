# Sidebars

Here we show the elements of sidebars that are specific to the type of
sidebar.

## **material** page, **word** list

Schematically:

```
selectbox colorpicker expand gloss lexeme
```

and when expanded the expansion is inserted below

```
additional properties of the word in short style
```

## **material** page, **queries** list

Schematically:

```
selectbox colorpicker expand user title
```

and when expanded the expansion is inserted below

```
big-area control full-title full-user
full-description
mql-query-instruction
```

## **material** page, **note sets** list

Schematically:

```
selectbox expand user keyword
```

and when expanded the expansion is inserted below

```
full-user
full-keyword
statistics for this chapter
```

## **record** page of type **word**

For all data versions

```
expand version CSV-icons chart-icon
```

and when expanded the expansion is inserted below

```
list of properties and values of the word
```

## **record** page of type **query**

```
link big-area-button
full-description
shared-status
```

Below that, for all data versions

```
expand version number-of-results
```

and when expanded the expansion is inserted below

```
csv-icons chart-icon mql-doc-link execute edit
mql-box
properties and values, among which the published status
```

and when editing there the area for the record increases and shows:

```
link
name-entry-box
description-markdown-entry-box
shared-control
```

and then per version

```
collapse csv-controls chart-control mql-doc-link execute save save-close cancel
mql-entry-box
properties and values, among which the published status
```

## **record** page of type **note set**

```
link
full-user
full-keyword
```

Below that, for all data versions

```
expand version csv-icons chart-icon
```

and when expanded the expansion is inserted below

```
the number of notes of this user and with this keyword in that version
```
