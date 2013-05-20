#############################################################################
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#############################################################################
#
#  Project Name        :    IEEE 802.11 Timeline Tool#                                                                            *
#
#  Author              :    Alex Ashley
#
#############################################################################

from HTMLParser import HTMLParser
import StringIO

def clean(string):
    okchars=' /.-_:?=()%'
    return ''.join([s for s in string if s.isalnum() or s in okchars])
            
class TableRow(object):
    def __init__(self):
        self.text = []
        self.anchors = []
        
    def add(self, item, anchor):
        self.text.append(item)
        self.anchors.append(anchor)
        
class TableHTMLParser(HTMLParser):
    """ Parses an HTML file, extracting tables. It returns them as a list of rows, 
    with each row containing a list of columns. Rowspan declarations in the HTML table
    are handled, and are converted to empty cells in spanned rows.
    """
    def __init__(self, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)
        self.anchor = ''
        self.active = False
        self.buffer = []
        self.item = None
        self.row = None
        self.rowspan = {}
        self.x=0
        self.y=0
        
    def handle_starttag(self, tag, attrs):
        if tag=='table':
            self.active = True
        if not self.active:
            return
        if tag=='a':
            for k,v in attrs:
                if k=='href':
                    self.anchor = v.replace(' ','%20')
        elif tag=='tr':
            self.row = TableRow()
            self.x = 0
        elif tag=='td' or tag=='th':
            try:
                ys,ye = self.rowspan[self.x]
                while self.y>=ys:
                    if self.y>=ye:
                        del self.rowspan[self.x]
                    if self.y<=ye:
                        self.row.add('','')
                        self.x += 1
                    ys,ye = self.rowspan[self.x]                        
            except KeyError:
                pass
            self.item = StringIO.StringIO()
            for k,v in attrs:
                if k=='rowspan':
                    self.rowspan[self.x] = (self.y+1,self.y+int(v)-1)

    def handle_data(self,data):
        if self.item is not None:
            data = clean(data)
            if data:
                self.item.write(data)
            
    def handle_endtag(self,tag):
        if tag=='table':
            self.active = False
        if not self.active:
            return
        if tag=='td' or tag=='th':
            s = self.item.getvalue().strip()
            self.row.add(s,self.anchor)
            self.x += 1
            self.item = None
            self.anchor = ''
        elif tag=='tr':
            self.buffer.append(self.row)
            self.row = None
            self.y += 1
        
