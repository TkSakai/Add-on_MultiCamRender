bl_info = {
    "name": "MultiCam Render",
    "author": "TkSakai",
    "version": (0, 1),
    "blender": (2, 79, 0),
    "location": "Property > Render ",
    "description": "Rendering with multiple cameras",
    "warning": "",
    "wiki_url": "",
    "category": "Render",
    }
        
import bpy
import os
import subprocess


### UI ###

class multicam_UL_List(bpy.types.UIList):
    
    def draw_item(self,context,layout,data,item,icon,active_data,active_propname,index):

        #name = item.name
        camOb = item.camOb
        layout = layout.split(0.4)
        row = layout.row()
        row.prop(camOb.data,"multicamactive",text="")
        row.prop(camOb,"name",icon = "CAMERA_DATA" ,translate = False,text="",emboss=False)
        
        
        if camOb.name in context.scene.objects:
            row = layout.row(align=True)
            row.prop(camOb.data,"currentframe",emboss=False)
            row.prop(camOb.data,"startframe",emboss=False,text="Start")
            row.prop(camOb.data,"endframe",emboss=False,text="End")
            
        else:
            row.label("Removed From Scene")
            
class RENDER_PT_multicamrenderPanel(bpy.types.Panel):
    bl_label = "MultiCam Render"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    
    def draw(self,context):
        scene = context.scene
        layout = self.layout
        row = layout.row(align=True)
        row.operator("render.multicamrender",text = "Render",icon="RENDER_STILL").anim = 0
        row.operator("render.multicamrender",text = "Animation",icon="RENDER_ANIMATION").anim = 1
        
        row=layout.row()
        row.template_list("multicam_UL_List","the_list",scene,"multicamlist",scene,"multicamindex",rows = 2)
        col = row.column(align = True)
        col.operator("multicamlist.new_item",text= "",icon = "ZOOMIN")
        col.operator("multicamlist.delete_item",text="",icon = "ZOOMOUT")
        col = layout.column()
        
        col.prop(scene,"multicammkdir",text="Make each folder")
 

### OPERATOR ####
   
class RENDER_OT_multicamrender(bpy.types.Operator):
    
    bl_idname="render.multicamrender"
    bl_label="render"
    bl_description ="Render with multiple camera"
    
    anim = bpy.props.BoolProperty()
    
    @classmethod
    def poll(self,context):
        return len(context.scene.multicamlist)
        
    def execute(self,context):
        defaultcamera = context.scene.camera
        defaultpath = context.scene.render.filepath
        defaultstart = context.scene.frame_start
        defaultend = context.scene.frame_end
        
        print ("MultiCam Render({}) --".format("Anim" if self.anim else "Still"))
        
        multicamlist = [item for item in context.scene.multicamlist if item.camOb.data.multicamactive]
        
        subprocess.Popen("explorer {}".format(defaultpath))
        
        for item in multicamlist:
            
            camOb = item.camOb
            
            if context.scene.multicammkdir :
                context.scene.render.filepath = defaultpath
                dirpath = os.path.join(context.scene.render.filepath,camOb.name)
            
                try:
                    os.makedirs(dirpath)
                except  FileExistsError:
                    pass
                except FileNotFoundError:
                    self.report({"ERROR"},"Check out output file path")
                
                context.scene.render.filepath = dirpath    
            
            try:      
                context.scene.camera = camOb
                
                filename = camOb.name + "_####" if self.anim else camOb.name
                context.scene.render.filepath = os.path.join(context.scene.render.filepath,filename)
                context.scene.frame_start = camOb.data.startframe
                context.scene.frame_end = camOb.data.endframe
            
                if self.anim == True:
                    
                    bpy.ops.render.render(animation=True)
                    
                if self.anim == False:
                    context.scene.frame_current = camOb.data.currentframe
                    bpy.ops.render.render(write_still=True,animation=False)                    
                                    
            except:
                self.report({"INFO"},"Invalid Camera in The List")
            
            finally:
                context.scene.render.filepath = defaultpath
        
        context.scene.render.filepath = defaultpath
        context.scene.camera = defaultcamera
        context.scene.frame_start = defaultstart
        context.scene.frame_end = defaultend
        
        return {"FINISHED"}
        


class RENDER_OT_multicamNewItem(bpy.types.Operator):
    
    bl_idname="multicamlist.new_item"
    bl_label = "Add"
    bl_description = "Add camera to list"
    
    def execute(self,context):
        for ob in bpy.context.selected_objects:                
            if ob.type == "CAMERA" and ob not in [item.camOb for item in bpy.context.scene.multicamlist]:
                
                item = context.scene.multicamlist.add()
                item.name = ob.name #just for bpy.context.scene.objects.__contains__
                item.camOb = ob 
                
                item.camOb.data.currentframe = context.scene.frame_current
            
        return{"FINISHED"}


class RENDER_OT_multicamDeleteItem(bpy.types.Operator):
    bl_idname = "multicamlist.delete_item"
    bl_label= "delete"
    bl_description = "Remove camera from list"
    
    @classmethod
    def poll(self,context):
        return len(context.scene.multicamlist) > 0
    def execute(self,context):
        list = context.scene.multicamlist
        index = context.scene.multicamindex
        
        list.remove(index)
        
        if index > 0:
            index = index - 1
        
        return {"FINISHED"} 
    

### PROPERTIES ###

class MultiCamListItem(bpy.types.PropertyGroup):
    
    name = bpy.props.StringProperty(name="",description = "",default="")
    camOb = bpy.props.PointerProperty(type=bpy.types.Object)

### REGISTER ####
    
clss = [RENDER_PT_multicamrenderPanel,RENDER_OT_multicamNewItem,RENDER_OT_multicamDeleteItem,MultiCamListItem,multicam_UL_List,RENDER_OT_multicamrender]

def register():
    
    startframe = bpy.context.scene.frame_start
    endframe = bpy.context.scene.frame_end    
    
    for cls in clss:
        bpy.utils.register_class(cls)

    bpy.types.Scene.multicamindex= bpy.props.IntProperty(name="index of multicam list",default = 0 )
    bpy.types.Scene.multicamlist = bpy.props.CollectionProperty(type=MultiCamListItem)
    bpy.types.Scene.multicammkdir = bpy.props.BoolProperty(default = True)
    
    
    bpy.types.Camera.startframe = bpy.props.IntProperty(name="StartFrame",default = startframe ,description = "For Animation Render")
    bpy.types.Camera.endframe = bpy.props.IntProperty(name="EndFrame",default = endframe ,description = "For Animation Render")
    bpy.types.Camera.currentframe = bpy.props.IntProperty(name="Frame",default = -1,description="For Still Render")
    bpy.types.Camera.multicamactive = bpy.props.BoolProperty(default = True)

    
def unregister():
    
    for cls in clss:
        bpy.utils.unregister_class(cls)
    
    
if __name__=="__main__":
    register()