bl_info = {
    "name": "ASCII Knots",
    "description": "Import ASCII art .knt files.",
    "author": "Shankar Sivarajan",
    "version": (0, 0, 5),
    "blender": (2, 93, 0),
    "location": "File > Import-Export",
    "category": "Import-Export"
}

### Knot parsing
from collections import defaultdict

char_dirs = {"^":(0,-1), "V":(0,1), ">":(1,0), "<":(-1,0), "O":(0,0)}
inv_dirs = {v:k for k,v in char_dirs.items()}

def nonempty(kmap, x, y):
        return [(x_off, y_off) 
                for x_off,y_off in char_dirs.values()
                if (x+x_off, y+y_off) in kmap]
    
# ^V>< move in this direction
# # invalid direction; this is an error
# U continue in current direction, but go underneath
# O stop; end of lead
# C check neighbours; must only be one neighbour not equal to current direction; take that
# L change label of lead (from the label map)
table = """
*   O ^ V > <
O   C # # # #
.   # . . . .
V   V # V U U
v   V # V U U
>   > U U > #
<   < U U # <
-   # U U > <
|   # ^ V U U
/   # > < ^ V
\   # < > V ^
+   # C C C C        
L   # L L L L
"""

# compute the table of possibilities
follow_map = {}
for line in table.splitlines():
    base_dirs = "O^V><"
    if len(line)>1:        
        chars = line.split()
        in_char,out_chars = chars[0], chars[1:]
        for i, c in enumerate(base_dirs):
            follow_map[(in_char, base_dirs[i])] = out_chars[i]
            
class KnotException(Exception):
    pass
    
class Knot:
    def parse_map(self, s):
        # convert from the ascii string to a dictionary of coordinates
        self.map = {}
        self.inv_map = defaultdict(list)
        self.labels = {}       
        self.crossovers = []
        self.lead_map = defaultdict(list)
        
        
        # represents a label object, that many
        # cells might refer to
        class Label:
            def __init__(self):
                self.label = ""
            def append(self, c):
                self.label += c            
                
        def mark_label(x,y):
            self.map[(x,y)] = 'L'
            self.inv_map['L'].append((x,y))
            self.labels[(x,y)] = label
                
        for y, line in enumerate(s.splitlines()):
            mark_invalid = False # clear invalid area flag
            for x, char in enumerate(line):
                
                if not mark_invalid:
                    # label 
                    if char=='[':
                        mark_invalid = True
                        label = Label()   # new label object                     
                        mark_label(x,y)                        
                    elif not char.isspace():
                        self.map[(x,y)] = char
                        self.inv_map[char].append((x,y))
                else:                    
                    if char==']':
                        # label finished; record it
                        mark_invalid = False
                        #self.labels[label_start] = line[label_start[0]+1:x]                    
                        mark_label(x,y)
                    else:
                        # mark these parts of the map as invalid
                        mark_label(x,y)
                        # and append to the label (reading left-to-right)
                        label.append(char)
                        
                    
    
                        
    def choose(self, x, y, dx, dy):
        """Return the neighbouring point that is going in a different direction,
        or throw an error if there is none or more than one."""
        neighbours = nonempty(self.map, x, y)        
        valid = [(vx, vy) for vx,vy in neighbours if not(vx==-dx and vy==-dy) and not(vx==0 and vy==0)]  
        
        
        
        if len(valid)<1:
            self.raise_error(x,y, "No neighbour to turn to")              
        if len(valid)>1:
             
            self.raise_error(x,y,"Ambiguous neighbour")            
        return valid[0]
    
    def find_heads(self):
        """Find each starting head"""                    
        heads = []
        
        # add in digit characters
        head_dirs = dict(char_dirs)
        head_dirs.update({str(d):(0,0) for d in range(10)})
        # handle both cases of V
        head_dirs["v"] = head_dirs["V"]
        
        
        # find all potential heads
        for char, (x_off,y_off) in head_dirs.items():
            locations = self.inv_map[char]
            for x,y in locations:                                
                if x_off==0 and y_off==0:
                    # undirected head
                    x_off, y_off = self.choose(x,y,0,0)
                    if char.isdigit():
                        # named head
                        heads.append((x,y,x_off,y_off,0,char))
                    else:
                        heads.append((x,y,x_off,y_off,0,""))
                else:
                    # check if this is a head (no space beforehand)
                    prev_lead = self.map.get((x-x_off, y-y_off), None)                        
                    if prev_lead is None:                        
                        heads.append((x,y,x_off,y_off,0,""))
                        
        # sort by y then x
        return sorted(heads, key=lambda x:(x[1], x[0]))
        
    def print_error(self, x, y, msg=""):
        """Print out a message with an error about the knot being parsed"""
        k = 3
        n = 6
        print(msg.center(n*2))
        for i in range(-n,n+1):
            for j in range(-n, n+1):
                if (abs(j)==k and abs(i)<k) or (abs(j)<k and abs(i)==k):
                    print("@", end="")
                else:
                    char = self.map.get((x+j,y+i))
                    char = char or " "
                    print(char, end="")
            print()
        raise KnotException(msg)
        
    def raise_error(self, x, y, msg=""):
        """Print out a message with an error about the knot being parsed"""
        k = 3
        n = 6
        str = [msg.center(n*2)]
        
        for i in range(-n,n+1):
            for j in range(-n, n+1):
                if (abs(j)==k and abs(i)<k) or (abs(j)<k and abs(i)==k):
                    str.append("@")
                    
                else:
                    char = self.map.get((x+j,y+i))
                    char = char or " "
                    str.append(char)
                    
            str.append("\n")
        raise KnotException("".join(str))
    
    def print_map(self, kmap):      
        """Print out the entire map, in canonical form."""
        def vrange(ix):
            vs = [pt[ix] for pt in kmap.keys()]
            return min(vs), max(vs)
        min_x, max_x = vrange(0)
        min_y, max_y = vrange(1)
        for i in range(min_y, max_y+1):
            for j in range(min_x, max_x+1):
                char = kmap.get((j,i))
                char = char or " "
                print(char, end="")
            print()
                
                                
    
    def trace_leads(self):
        heads = self.find_heads()        
        
        self.leads = []
        self.over_map = defaultdict(list)
        ix = 0
        # trace each lead, starting from each head found
        for head in heads:
            lead = []
            x,y,dx,dy,z,name = head
                 
            lead.append((x,y,dx,dy,z,name))
            x,y = x+dx, y+dy
            while (x,y) in self.map:                
                char = self.map.get((x,y))                
                # where we are going now (as a character)
                dir_char = inv_dirs[(dx,dy)]
                
                action = follow_map.get((char, dir_char))
                # simple change of direction
                if action in char_dirs:
                    dx, dy = char_dirs[action]
                    z = 0
                elif action=='L':
                    # rename lead
                    name = self.labels[(x,y)].label
                elif action=='U':
                    # dx,dy don't change
                    z = -1
                    self.crossovers.append((x,y))
                    
                elif action=='C':
                    dx, dy = self.choose(x,y,dx,dy)
                    z = 0
                elif action=='.':
                    break
                elif action=='#':
                    self.raise_error(x,y, "Invalid direction") 
                elif action is None:
                    self.raise_error(x,y,"Character %s unexpected"%char)
                    
                lead.append((x,y,dx,dy,z,name))
                self.over_map[(x,y)].append((ix, dx, dy, z))
                # record where we are in the lead map
                self.lead_map[(x,y)].append((lead, ix))
                ix += 1
                x, y = x+dx, y+dy
            self.leads.append(lead)
               
            
    def show_lead(self, lead):
        kmap = {}
        for x,y,dx,dy,z,name in lead:
            if dx==0 and (x,y) not in kmap:
                kmap[(x,y)] = '|'
            elif  (x,y) not in kmap:
                kmap[(x,y)] = '-'
            elif (x,y) in kmap:
                kmap[(x,y)] = '+'            
                        
        self.raise_map(kmap)
        
    def show_lead_directed(self, lead):
        kmap = {}
        for x,y,dx,dy,z,name in lead:
            char = inv_dirs[(dx,dy)]
            kmap[(x,y)] = char
                        
        self.print_map(kmap)
        
    def show_all_leads_directed(self):
        kmap = {}
        for lead in self.leads:
            for x,y,dx,dy,z,name in lead:
                char = inv_dirs[(dx,dy)]
                kmap[(x,y)] = char
                            
        self.print_map(kmap)
        
    def __init__(self, s):
        """Take a string representation of a knot, and fill 
        in the knot data from the string."""
        # generate map of characters
        self.parse_map(s)
        self.trace_leads()
        
        
               
    def is_crossing(self, x, y):
        print((x,y))
        cross = self.over_map.get((x,y))
        return cross is not None and len(cross)>1
    
       
        
        
### END knot parsing

### Blender Python interface
import bpy
from bpy_extras.io_utils import ImportHelper

from mathutils import Vector

class ImportKnot(bpy.types.Operator, ImportHelper):
    bl_idname = "import_knot.knt"
    bl_label = "Import Knot"
    
    bl_description = "Import knot"
    # bl_options = {'UNDO'}
  
    filename_ext = ".knt", ".txt";
  
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
  
    filter_glob: bpy.props.StringProperty(
        default="*.knt",
        options={"HIDDEN"},
    )
  
    @classmethod
    def poll(cls, context):
      return True
  
    def execute(self, context):
        
        filename = self.filepath
        
        with open(filename, "r") as knot_file:
            knot_obj = Knot(knot_file.read())
        
        
        ix = 0
        verts = []
        edges = []
        
        bias = 0
        z_scale = 1
        
        if len(knot_obj.leads)<1:
            raise KnotException("Warning: no valid knot found")        
        
        for lead in knot_obj.leads:
            prev = None
            for x,y,dx,dy,z,name in lead:
                if knot_obj.is_crossing(x,y):
                    if z==-1:
                        verts.append(Vector((x,-y,-z_scale * (bias+1)/2)))
                    else:
                        verts.append(Vector((x,-y,z_scale*  (bias+1)/2)))                    
                else:
                    verts.append(Vector((x,-y,0)))
                    
                if prev is not None:
                    edges.append((prev, ix))
                prev = ix
                ix += 1

                 
        name = bpy.path.display_name_from_filepath(filename)
        me = bpy.data.meshes.new(name)
          
        me.from_pydata(verts, edges, [])
          
        ob = bpy.data.objects.new(name, me)
          
        col = bpy.context.collection
        col.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        
        # First separate by loose parts, and iterate the following modifiers over each.
        
        # ob.modifiers.new("Subsurface", type='SUBSURF')
        # bpy.context.object.modifiers["Subsurface"].levels = 2


        # ob.modifiers.new("Skin", type='SKIN')
        
        # ob.modifiers.new("Subsurface", type='SUBSURF')
        # bpy.context.object.modifiers["Subsurface"].levels = 1

        
        return {'FINISHED'}
  
    def draw(self, context):
        pass


def menu_import(self, context):
    self.layout.operator(ImportKnot.bl_idname, text="Knot (.knt)")
    
def register():
    bpy.utils.register_class(ImportKnot)
    
    bpy.types.TOPBAR_MT_file_import.append(menu_import)

def unregister():
    
    bpy.utils.unregister_class(ImportKnot)
    
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
  
if __name__ == "__main__":
  register()

    
    
