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

table.presentation {
    border-style:hidden;
}

table.presentation tr {
    border-style:hidden;
}

table.presentation th {
    padding:0px 15px 0px 0px;
    border-style:hidden;
    text-align:center;
}

table.presentation td {
    padding:0px 5px 0px 0px;
    border-style:hidden;
}

table.presentation td.unicode {
    text-align:right;
    font-family:SBL Hebrew;
}

table.categories {
    margin-left: auto;
    margin-right: auto;
}

table.categories, table.categories tr, table.categories th, table.categories td {
    border-style:hidden;
    color: Maroon;
}

div.navigation {
    margin:auto;
    width:50%;
    font-size:small;
    font-style:italic;
}

div.navigation form, div.navigation form input {
    display: inline;
}

form input {
    max-width: 30px;
}

div.button form input {
	max-width:100%;
}

div.button {
	max-width:15%;
	margin:auto;
}

div.output {
    font-size: small;
    z-index:0;
}

div.front, div.front_a, div.front_b {
    color: Crimson;
}

div.front, div.front_a {
	text-align: center;
}

div.front_b div, div.front_a div {
    display: none;
} 

div.front div, div.front_hebrew div {
    display: none;
    position: relative;
}

div.front:hover div, div.front_a:hover div, div.front_b:hover div {
    display: block;
    max-width: 200px;
}
    
div.front_hebrew:hover div {
    display: block;
}

div.def_disc, div.factors {
    font-size: x-small;
    background-color:White;
    z-index:1;
    position:absolute;
    font-family:SBL Hebrew;
    line-height: 95%;
}

div.translation {
    z-index:1;
    position:absolute;
    right:10%;
    line-height: 90%;
    font-size: x-small;
}

div.left {
    border-left-style:dotted;
    border-left-width:thin;
}

div.right {
    border-right-style:dotted;
    border-right-width:thin;
}

div.delimit {
	border-top-width: thin;
	border-top-style: dotted;
}

span.translation_verb{
    color: Crimson;
}

span.verb {
    color: Crimson;
}

div.small {
    font-size: xx-small;	
	line-height: 95%;
}

div.counter {
	font-size: small;
	font-style: italic;
}

span.count {
    text-align: left;
}

</style>
"""))

# <codecell>

import sys
import re

def read_lines(lines):
    data = []
    for line in lines:
        data_in_line = re.split(';',line)
        data.append(data_in_line)
    return data

def read_file(file):
    f = open(file, 'r')
    lines = []

    for line in f:
        lines.append(line)

    f.close()
    return read_lines(lines)

def create_conversion_dict():
    return {'>': "\u05D0",
            'B': "\u05D1",
            'G': "\u05D2",
            'D': "\u05D3",
            'H': "\u05D4",
            'W': "\u05D5",
            'Z': "\u05D6",
            'X': "\u05D7",
            'V': "\u05D8",
            'J': "\u05D9",
            'K': "\u05DB",
            'L': "\u05DC",
            'M': "\u05DE",
            'N': "\u05E0",
            'S': "\u05E1",
            '<': "\u05E2",
            'P': "\u05E4",
            'Y': "\u05E6",
            'Q': "\u05E7",
            'R': "\u05E8",
            'C': "\u05E9\u05C1",
            'F': "\u05E9\u05C2",
            'T': "\u05EA",
            'p': "\u05E3",
            'm': "\u05DD",
            'n': "\u05DF",
            'k': "\u05DA",
            'y': "\u05E5",
            '_': "\u002D",
            '-': "\u002D",
            '[': "\u005B",
            ']': "\u005D",
            '/': "/",
            ' ': " ",
            '\0': "",
			'=': "",
            '(': "\u0028",
            ')': "\u0029"}

def test_final_character(c):
    if c == 'P':
        return 'p'
    elif c == 'M':
        return 'm'
    elif c == 'N':
        return 'n'
    elif c == 'K':
        return 'k'
    elif c == 'Y':
        return 'y'
    else:
        return c

def set_word_to_unicode(sp, conversion):
    i = 1
    result = ""
    for c in sp:
        if i == len(sp) or (i == (len(sp) - 1) and sp[-1] == ')'):
            c = test_final_character(c)
        result += (conversion[c])
        i += 1
    return result
        
def analyze_phrase(subphrases, conversion):
    phrasesNew = ""
    result = ""

    if (len(subphrases) > 1):
        i = 0
        while (i < (len(subphrases) - 1)):
            phrasesNew += (set_word_to_unicode(subphrases[i], conversion) + " ")
            i += 1
        label = subphrases[len(subphrases) - 1]
        result = label + " " + phrasesNew
    else:
        sf = re.split('-', subphrases[0])
        result = sf[1] + " -" + set_word_to_unicode(sf[0], conversion)
        
    return result

def analyze_phrases(phrases, conversion):
    final_result = ""
    i = 0
    
    for phrase in reversed(phrases):
        phrase = phrase.replace("]", "")
        final_result += "[" + analyze_phrase(phrase[1:].split(), conversion).strip() + "] "
    return final_result

def set_to_unicode(transcription, max_line_length, conversion):
    result = ""
    start_of_line = ""
    i = 0
    for c in transcription:
        if c == '[':
            break
        start_of_line += c
        i += 1
    rest_of_line = transcription[i:]
    whitespace = (max_line_length - len(transcription)) * " "
    result += whitespace + analyze_phrases(rest_of_line.split('] '), conversion) + (''.join(reversed(start_of_line)))
    return result

def calculate_max_length(data):
    result = 0
    for d in data:
        transcription = d[20]
        if len(transcription) > result:
            result = len(transcription)
    return result
        
def analyze_transcription(data, conversion):
    unicode_lines = []
    max_line_length = calculate_max_length(data)
    for d in data:
        transcription = d[20]
        unicode_heb = set_to_unicode(transcription, max_line_length, conversion)
        unicode_lines.append(unicode_heb)
    return unicode_lines

def getTranslation(translation, verb):
    if translation == "":
        return "---"
    result = ""
    sign = ""
    inMDM = False
    translation = translation.strip()
    translation = translation.replace(">", "&gt;")
    translation = translation.replace("<", "&lt;")
    translation_list = re.split(' ',translation)
    translation_verb = verb.split()
    for word in translation_list:
        if len(word) > 1 and (word[-1] == '!' or word[-1] == '?'):
            sign = word[-1]
            word = word[:-1]
        if word[0] == '(':
            inMDM = True
        if word[-1] == ')':
            inMDM = False
        if (word in translation_verb) and not inMDM:
            result += '<span class="translation_verb">' + word + '</span>' + sign + ' '
        else:
            result += word + sign + ' '
    return result

def get_hebrew_in_unicode(line):
    unicode_line_temp = line.replace("<", "&lt;")
    unicode_line_temp2 = unicode_line_temp.replace(">", "&gt;")
    unicode_line_temp3 = unicode_line_temp2.replace(" ", "&nbsp;")
    #in order to distinguish between '< >' of tags and '< >' of constituent labels:
    unicode_line_temp4 = unicode_line_temp3.replace("!", '<span class="verb">') 
    unicode_line_temp5 = unicode_line_temp4.replace("?", "</span>")
    return (unicode_line_temp5)

def identify_verb(line, tp):
    result = ""
    phrases = line.split("]")
    i = 0
    for p in phrases:
        i += 1
        if i == len(phrases):
            result += p
        elif (("<Pr>" in p) or ("<PO>" in p) or (tp == "Ptcp" and "[<PC>" in p)):
            result += '!' + p + ']?' + " "
        else:
            result += p + "] "
    
    return result

def make_translation(data, unicode_lines, n):
    total = '<table class="presentation" id="Translation">'
    head = '<tr><th>' + '</th><th><a href="HebrewText.ipynb" target="_blank">' + "Hebrew text" + '</a></th><th><a href="ClauseLabels.ipynb" target="_blank">' + "ClTp" + '</a></th><th><a href="Translation.ipynb" target="_blank">' + "Translation" + '</a></th></tr>'
    total += head
    verse_label = ""
    i = 0
    
    for d in data:
        current_verse = d[0]
        if current_verse == verse_label:
            current_verse = ""
        else:
            verse_label = current_verse
        unicode_line_with_marked_verb = identify_verb(unicode_lines[i], d[2])
        unicode_line_with_spaces = get_hebrew_in_unicode(unicode_line_with_marked_verb)
        start = ""
        for c in d[20]:
            if c == '[':
                break
            start += c
        start_with_spaces = get_hebrew_in_unicode(start)

        line = '<tr><td>' + current_verse + '</td><td class="unicode" nowrap>' + unicode_line_with_spaces + '</td><td style="font-family:Courier">' + d[2] + '</td><td nowrap>' + start_with_spaces + getTranslation(d[21],d[22]) + '</td></tr>'
        total += line
        i += 1
        if (i == n):
            break
    
    total += '</table>'
    display(HTML(total))

def setFU(fu):
    if fu == "non-vol.":
        return "non-volitive"
    elif fu == "juss.":
        return "jussive"
    elif fu == "coh.":
        return "cohortative"
    elif fu == "volit.":
        return "volitive"
    elif fu == "final":
        return "final"
    elif fu == "neg.fin.":
        return "negative final"
    elif fu == "neg.vol.":
        return "negative volitive"
    elif fu == "prohib.":
        return "prohibitive"
    elif fu == "consec.":
        return "consecutive"
    else:
        return "indicative"

def setMORPH(morph):
    if morph == "juss.":
        return "jussive"
    else:
        return "cohortative"
    
def setBLOCK(block):
    if block == "attr.":
        return "an attributive"
    elif block == "constit.":
        return "a constituent"
    else:
        return "?"

def setProcesses(morph, defFu, inhtbFu, inhFu, bloFu, finFu, MDM, conversion):
    result = ""
    if (MDM != "" and MDM[0] == '('):
        MDM = MDM[1:-1]
    if morph != "":
        if defFu == "non-vol.":
            result = "Morphological marking as " + setMORPH(morph) + " overrules non-volitive default function"
        else:
            result = "Morphological marking as " + setMORPH(morph) + " confirms " + setFU(defFu) + " default function"
    elif bloFu != "":
        if (bloFu == "attr." or bloFu == "constit."):
            result = "This 0-yiqtol clause is " + setBLOCK(bloFu) + " clause and therefore does not fulfill its default " + setFU(defFu) + " function."
        elif bloFu == "precDrSp":
            result = "This 0-yiqtol clause introduces the preceding direct speech section, which should be seen as the 0-yiqtol verb's object. Therefore the clause does not fulfill its " + setFU(defFu) + " default function."
        elif bloFu == "narr":
            result = "This verb-initial yiqtol clause is embedded in a narrative domain of communication and therefore does not fulfill its " + setFU(defFu) + "  default function."
        elif bloFu == "prosp":
            result = "This 0-yiqtol clause is embedded in a prospective domain of communication and therefore does not fulfill its " + setFU(defFu) + "  default function."
        elif bloFu == "inhExpSu":
            result = "This 0-yiqtol clause inherits its mother's explicit subject, should therefore be reanalyzed as an (X-)yiqtol clause and so does not fulfill its " + setFU(defFu) + "  default function."
        else:
            result = "This yiqtol clause inherits the multiple-duty modifier " + set_word_to_unicode(MDM, conversion) + " and so does not fulfill its " + setFU(defFu) + "  default function."    
    elif inhFu != "":
        if inhFu == inhtbFu:
            if inhFu == "vol.pair":
                result = "The clause forms a volitive pair together with its volitive <em>weyiqtol</em> daughter clause. The " + setFU(defFu) + " default function is overridden by a volitive one."
            elif inhFu == defFu:
                result = "The non-volitive default function of this weQatal-clause is preserved as the clause inherits non-volitive functionality."
            elif inhFu == "final" and defFu != "non-vol.":
                result = "Inheritance of " + setFU(inhtbFu) + " functionality is possible and does indeed take place."			
            else:
                result = "Inheritance of " + setFU(inhtbFu) + " functionality is possible and does indeed take place. The " + setFU(defFu) + " default function is overridden."
        elif inhFu == "neg.fin." or inhFu == "neg.vol.":
                result = "Inheritance of " + setFU(inhFu) + " functionality is possible and does indeed take place. The " + setFU(defFu) + " default function is overridden." 
        elif inhFu != "x":
                print("Error in process! " + inhFu + inhtbFu)
        else:
            if inhtbFu == "vol.pair":
                result = "The clause could have formed a volitive pair together with its volitive <em>weyiqtol</em> daughter clause, but this is not the case. The " + setFU(defFu) + " default function is not overridden."
            else:
                result = "Inheritance of " + setFU(inhtbFu) + " functionality is possible, but does not take place. The " + setFU(defFu) + " default function is not overridden."
    else:
        result = ""
    if (result != ""):
        return '<td><div class="front_a">!<div class="factors">' + result + '</div></div></td>'
    else:
        return '<td>  ' + '</td>'

def setDefDisc(toc, loc, psp, anch, conversion):
    result = ""
    if (psp == ""):
        if (loc == ""):
            return ""
        else:
            result = (toc + '-' + loc)
    else:
        result = (toc + '-' + loc + '-' + psp)
    if (anch != ""):
        result += ";<br>The clause contains or inherits the mainline anchor " + set_word_to_unicode(anch, conversion) + "."
    return result

def setPatternNumber(nr):
    if (nr == '0'):
        return '<td>&nbsp;</td>'
    else:
        return '<td><a href="ConcordanceOfPatterns.ipynb#' + nr + '" target="_blank">' + nr + '</a></td>'

def make_analysis(data, unicode_lines, conversion, n):
    total = '<table class="presentation" id="Analysis">'
    head = '<tr><th>' + "Vs" + '</th><th>' + "Ln" + '</th><th nowrap><a href="HebrewText.ipynb" target="_blank">' + "Hebrew text" + '</a><br><div class="small">' + "(mouse-over for " + '<a href="Translation.ipynb" target="_blank">' + "Translation)" + '</a></div></th><th nowrap><a href="ClauseLabels.ipynb" target="_blank">' + "ClTp" + '</a><br><div class="small">' + "(mouse-over<br>for<br>" + '<a href="DefaultDiscourseFunctions.ipynb" target="_blank">' + "DefDiscFu)" + '</a></div></th><th><a href="DefaultFunctions.ipynb" target="_blank">' + "DefFu" + '</a></th><th><a href="Processes.ipynb" target="_blank">' + "Processes" + '</a><br><div class="small">' + '(hover over<br>"!"-sign)' + '</div></th><th><a href="FinalFunctions.ipynb" target="_blank">' + "FinFu" + '</a></th><th><a href="MDModifier.ipynb" target="_blank">' + "MDMod" + '</a></th><th><a href="CCR.ipynb" target="_blank">' + "CCR" + '</a></th><th><a href="DiscourseFunctions.ipynb" target="_blank">' + "DiscFu" + '</a></th><th><a href="ConcordanceOfPatterns.ipynb" target="_blank">' + "#Pat" + '</a></th></tr>'
    total += head
    i = 0
    
    for d in data:
        unicode_line_with_spaces = get_hebrew_in_unicode(unicode_lines[i])
        processes = setProcesses(d[8], d[7], d[9], d[10], d[12], d[13], d[11], conversion)
        df = setDefDisc(d[14], d[15], d[16], d[17], conversion)
        patternNumber = setPatternNumber(d[6])		
        line = '<tr id="ln' + str(i+1) + '"><td>' + d[0] + '</td><td>' + d[4] + '</td><td class="unicode" nowrap><div class="front_hebrew">' + unicode_line_with_spaces + '<div class="translation">' + getTranslation(d[21], d[22]) + '</div></div></td><td><div class="front">' + d[2] + '<div class="def_disc">' + df + '</div></div></td><td><div class="left">' + d[7] + '</div></td>' + processes + '<td><div class="right">' + d[13] + '</div></td><td class="unicode">' + set_word_to_unicode(d[11], conversion) + '</td><td>' + d[3] + '</td><td>' + d[18] + '</td>' + patternNumber + '</tr>'
        total += line
        i += 1
        if (i == n):
            break
    
    total += '</table>'
    
    display(HTML(total))

def getModifier(s):
    result = ""
    for c in s:
        if c != '(':
            result += c
        else:
            break
    return result

def getMDM(s):
    i = 0
    for c in s:
        if c == '(':
            return s[i:]
        i += 1
    return ""
    
def setModifier(s, conversion):
    modifier = getModifier(s)
    MDM = getMDM(s)
    if (modifier != "" and MDM != ""):
        return '<td class="unicode" nowrap><div class="right">' + set_word_to_unicode(modifier, conversion) + "" + set_word_to_unicode(MDM, conversion) + '&#8207;</div></td>'
    elif (modifier != ""):
        return '<td class="unicode" nowrap><div class="right">' + set_word_to_unicode(modifier, conversion) + '</div></td>'
    elif (MDM != ""):
        return '<td class="unicode" nowrap><div class="right">' + set_word_to_unicode(MDM, conversion) + '</div></td>'
    else:
        return '<td><div class="right">&nbsp;</div></td>'	
   
def set_agent_parameters(agent):
    if (agent == "newAgent"):
        return "The daughter clause has as its subject a new animate participant."
    elif (agent == "nwPtcpSet"):
        return "The daughter clause introduces a new set of participants."
    else:
        return "Mother and daughter clause are parallel."
    
def setParticipants(agent, ptcp):
    if (agent != ""):
        return '<td><div class="front_b">' + ptcp + '<div class="factors">' + set_agent_parameters(agent) + '</div></div></td>'
    else:
        return '<td>  ' + ptcp + '</td>'
            
def make_patterns(patterns, conversion, n, conc):
    total = '<table class="presentation" id="Patterns">'
    if (conc == "yes"):
        head = '<tr><th>' + "#Pat" + '</th><th>' + "Vs" + '</th><th>' + "Ln" + '</th><th nowrap><a href="ClauseLabels.ipynb" target="_blank">' + "ClTp" + '</a><br><div class="small">' + "(mouse-over<br>for<br>" + '<a href="DefaultDiscourseFunctions.ipynb" target="_blank">' + "DefDiscFu)" + '</a></div></th><th nowrap><a href="HebrewText.ipynb" target="_blank">' + "Hebrew text" + '</a><br><div class="small">' + "(mouse-over for " + '<a href="Translation.ipynb" target="_blank">' + "Translation)" + '</a></div></th><th><a href="CCR.ipynb" target="_blank">' + "CCR" + '</a></th><th><a href="DefaultFunctions.ipynb" target="_blank">' + "DefFu" + '</a></th><th><a href="Processes.ipynb" target="_blank">' + "Processes" + '</a><br><div class="small">' + '(hover over<br>"!"-sign)' + '</div></th><th><a href="FinalFunctions.ipynb" target="_blank">' + "FinFu" + '</a></th><th nowrap><a href="MDModifier.ipynb" target="_blank">' + "Mod-MDM" + '</a></th><th><a href="Participants.ipynb" target="_blank">' + "Ptcp" + '</a></th><th><a href="DiscourseFunctions.ipynb" target="_blank">' + "DiscFu" + '</th></tr>'
    else:
        head = '<tr><th><a href="ConcordanceOfPatterns.ipynb" target="_blank">' + "#Pat" + '</a></th><th>' + "Vs" + '</th><th>' + "Ln" + '</th><th nowrap><a href="ClauseLabels.ipynb" target="_blank">' + "ClTp" + '</a><br><div class="small">' + "(mouse-over<br>for<br>" + '<a href="DefaultDiscourseFunctions.ipynb" target="_blank">' + "DefDiscFu)" + '</a></div></th><th nowrap><a href="HebrewText.ipynb" target="_blank">' + "Hebrew text" + '</a><br><div class="small">' + "(mouse-over for " + '<a href="Translation.ipynb" target="_blank">' + "Translation)" + '</a></div></th><th><a href="CCR.ipynb" target="_blank">' + "CCR" + '</a></th><th><a href="DefaultFunctions.ipynb" target="_blank">' + "DefFu" + '</a></th><th><a href="Processes.ipynb" target="_blank">' + "Processes" + '</a><br><div class="small">' + '(hover over<br>"!"-sign)' + '</div></th><th><a href="FinalFunctions.ipynb" target="_blank">' + "FinFu" + '</a></th><th nowrap><a href="MDModifier.ipynb" target="_blank">' + "Mod-MDM" + '</a></th><th><a href="Participants.ipynb" target="_blank">' + "Ptcp" + '</a></th><th><a href="DiscourseFunctions.ipynb" target="_blank">' + "DiscFu" + '</th></tr>'
    total += head
    patternNumber = 0
    patternNumberWholePattern = 0
    numberOfOccurrences = 0
    numberOfOccurrencesPattern = 0
    totalNumberOfOccurrences = 0
    
    for p in patterns:
        if (n != 0 and int(p[0]) != n):
            continue
        default_df_mother = setDefDisc(p[31], p[32], p[33], p[29], conversion)
        default_df_daughter = setDefDisc(p[34], p[35], p[36], p[30], conversion)
        mother_modifier = setModifier(p[19], conversion)
        daughter_modifier = setModifier(p[20], conversion)
        processes_mother = setProcesses(p[23], p[9], p[11], p[13], p[15], p[17], getMDM(p[19]), conversion)
        processes_daughter = setProcesses(p[24], p[10], p[12], p[14], p[16], p[18], getMDM(p[20]), conversion)
        participants = setParticipants(p[27], p[28])
        mother_unicode_line_with_spaces = get_hebrew_in_unicode(set_to_unicode(p[41], len(p[41]), conversion))
        daughter_unicode_line_with_spaces = get_hebrew_in_unicode(set_to_unicode(p[44], len(p[44]), conversion))
        mother_ctt_text = (mother_unicode_line_with_spaces)[:(mother_unicode_line_with_spaces).rfind(']') + 1]
        daughter_ctt_text = (daughter_unicode_line_with_spaces)[:(daughter_unicode_line_with_spaces).rfind(']') + 1]
        
        if (conc == "yes"):
            lineMother = '<tr><td>' + p[0] + '</td><td><a href="Psalm' + str(p[1][2:5]) + '.ipynb" target="_blank">' + p[1] + '</a></td><td>' + p[4] + '</td><td><div class="front">' + p[3][:4] + '<div class="def_disc">' + default_df_mother + '</div></div></td><td class="unicode" nowrap><div class="front_hebrew">' + mother_ctt_text + '<div class="translation">' + getTranslation(p[39], p[40]) + '</div></div></td><td>' + p[7]  + '</td><td nowrap><div class="left">' + p[9] +'</div></td>' + processes_mother + '<td nowrap><div class="right">' + p[17] + '</div></td>' + mother_modifier + '<td></td><td>' + p[37] + '</td></tr>' 
            lineDaughter = '<tr><td></td><td></td><td>' +  p[5] + '</td><td><div class="front">' + p[3][6:] + '<div class="def_disc">' + default_df_daughter + '</div></div></td><td class="unicode" nowrap><div class="front_hebrew">' + daughter_ctt_text + '<div class="translation">' + getTranslation(p[42], p[43]) + '</div></div></td><td>' + p[8] + '</td><td nowrap><div class="left">' + p[10] + '</div></td>' + processes_daughter + '<td nowrap><div class="right">' + p[18] + '</div></td>' + daughter_modifier + participants + '<td>' + p[38] + '</td></tr>'
        else:
            lineMother = '<tr><td><a href="ConcordanceOfPatterns.ipynb#' + p[0] + '" target="_blank">' + p[0] + '</a></td><td>' + p[1] + '</td><td><a href="#ln' + p[4] + '">' + p[4] + '</a></td><td><div class="front">' + p[3][:4] + '<div class="def_disc">' + default_df_mother + '</div></div></td><td class="unicode" nowrap><div class="front_hebrew">' + mother_ctt_text + '<div class="translation">' + getTranslation(p[39], p[40]) + '</div></div></td><td>' + p[7]  + '</td><td nowrap><div class="left">' + p[9] +'</div></td>' + processes_mother + '<td nowrap><div class="right">' + p[17] + '</div></td>' + mother_modifier + '<td></td><td>' + p[37] + '</td></tr>' 
            lineDaughter = '<tr><td></td><td></td><td><a href="#ln' + p[5] + '">' +  p[5] + '</a></td><td><div class="front">' + p[3][6:] + '<div class="def_disc">' + default_df_daughter + '</div></div></td><td class="unicode" nowrap><div class="front_hebrew">' + daughter_ctt_text + '<div class="translation">' + getTranslation(p[42], p[43]) + '</div></div></td><td>' + p[8] + '</td><td nowrap><div class="left">' + p[10] + '</div></td>' + processes_daughter + '<td nowrap><div class="right">' + p[18] + '</div></td>' + daughter_modifier + participants + '<td>' + p[38] + '</td></tr>'		
        if (conc == "yes" and patternNumber != 0 and int(p[0]) != patternNumber):
            if patternNumber == 1731:
                total += '<tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan = "5"><strong><em>' + '128 occurrences (Psalm titles not included)(' + str(round((128 / 4805 * 100), 2)) + '%)</em></strong></td></tr>'
            else:			
                total += '<tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan = "5"><strong><em>' + str(numberOfOccurrences) + ' occurrences (' + str(round((numberOfOccurrences / 4805 * 100), 2)) + '%)</em></strong></td></tr>'
            if (patternNumberWholePattern != 0 and ((int(p[0]) // 10) != patternNumberWholePattern)):
                total += '<tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan = "5"><strong><em>' + str(numberOfOccurrencesPattern) + ' occurrences of whole pattern (' + str(round((numberOfOccurrencesPattern / 4805 * 100), 2)) + '%)</em></strong></td></tr>'
                numberOfOccurrencesPattern = 0            
            total += '<tr><td><div class="delimit"></div></td><td><div class="delimit"></div></td><td><div class="delimit"></div></td><td><div class="delimit"></div></td><td><div class="delimit"></div></td><td><div class="delimit"></div></td><td><div class="delimit"></div></td><td><div class="delimit"></div></td><td><div class="delimit"></div></td><td><div class="delimit"></div></td><td><div class="delimit"></div></td><td><div class="delimit"></div></td></tr><tr id="' + p[0] + '"><td>&nbsp;</td></tr>'
            numberOfOccurrences = 0
        total += lineMother + lineDaughter + '<tr><td>&nbsp;</td></tr>'
        patternNumber = int(p[0])
        patternNumberWholePattern = int(p[0]) // 10
        numberOfOccurrences += 1
        numberOfOccurrencesPattern += 1
        totalNumberOfOccurrences += 1		
		
    if (conc == "yes"):
        total += '<tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan = "5"><strong><em>' + str(numberOfOccurrences) + ' occurrences (' + str(round((numberOfOccurrences / 4808 * 100), 2)) + '%)</em></strong></td></tr>'
        total += '<tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan = "5"><strong><em>' + '247 occurrences of whole pattern (' + str(round((247 / 4805 * 100), 2)) + '%)</em></strong></td></tr>'	
    total += '</table>'
    
    display(HTML(total))
	
def print_translation(analysisFile, numberOfLines=0):
    data = read_file(analysisFile)
    conversion_to_utf8 = create_conversion_dict()
    unicode_lines = analyze_transcription(data, conversion_to_utf8)
    make_translation(data, unicode_lines, numberOfLines)
    
def print_analysis(analysisFile, numberOfLines=0):
    data = read_file(analysisFile)
    conversion_to_utf8 = create_conversion_dict()
    unicode_lines = analyze_transcription(data, conversion_to_utf8)
    make_analysis(data, unicode_lines, conversion_to_utf8, numberOfLines)

def print_patterns(patternsFile, patternNumber=0, conc="no"):
    patterns = read_file(patternsFile)
    conversion_to_utf8 = create_conversion_dict()
    make_patterns(patterns, conversion_to_utf8, patternNumber, conc)

