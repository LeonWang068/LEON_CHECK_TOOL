#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import maya.cmds as cmds
import oss2
import os
import sys

__author__ = 'LeonWang'

def all_files(config_dict = {}):
    file_dict = {}    
    for key in config_dict.keys():
        temp_list = []
        for node in cmds.ls(type = key):
            for i in config_dict[key]:
                temp_path = eval(i)
                if temp_path != "":
                    if os.path.isfile(temp_path) and temp_path not in file_dict.keys():
                        file_dict[temp_path] = {}
                        file_dict[temp_path]["node"] = []
                        file_dict[temp_path]["id"] = -1
                        file_dict[temp_path]["oss_path"] = path_osspath(temp_path,root="I:/")
                        file_dict[temp_path]["status"] = ""
                        file_dict[temp_path]["node"].append(node)
                    elif os.path.isfile(temp_path) and temp_path in file_dict.keys():
                        file_dict[temp_path]["node"].append(node)
                    elif os.path.isdir(temp_path) is False:
                        local_temp_path = os.path.dirname(temp_path)
                        local_temp_filename = os.path.basename(temp_path)
                        pre = local_temp_filename.split('.')[0]
                        for f in os.listdir(local_temp_path):
                            if "%s."%pre in f:
                                temp_fpath = os.path.join(local_temp_path,f).replace("\\","/")
                                if temp_fpath in file_dict.keys():
                                    file_dict[temp_fpath]["node"].append(node)
                                else:
                                    file_dict[temp_fpath] = {}
                                    file_dict[temp_fpath]["node"] = []
                                    file_dict[temp_fpath]["id"] = -1
                                    file_dict[temp_fpath]["oss_path"] = path_osspath(temp_fpath,root="Z:/")
                                    file_dict[temp_fpath]["status"] = ""
                                    file_dict[temp_fpath]["node"].append(node)
    i=0
    for path in file_dict.keys():
        file_dict[path]["id"] = i
        i+=1
    return file_dict

def path_osspath(path,root=""):
    return path.replace(root,'')
    
def get_file_size(path):
    filePath = path
    fsize = os.path.getsize(filePath)
    return fsize

def get_ossfile_size(path,bucket):
    simplifiedmeta = bucket.get_object_meta(path)
    return simplifiedmeta.headers['Content-Length']
        

def check(path,oss_path,bucket):
    exist = bucket.object_exists(oss_path)
    if not exist:
        return False
    elif int(get_file_size(path))!= int(get_ossfile_size(oss_path,bucket)):
        return False
    else:
        return True

def check_button(bucket):
    global files_dict
    for key in files_dict.keys():
        if check(key,files_dict[key]["oss_path"],bucket) is True:
            cmds.text(eval('control_status_' + str(files_dict[key]["id"])),edit=True,ebg=True,bgc=[0.0,1.0,0.0],l="Y")
            files_dict[key]["update"] = "Y"
        else:
            cmds.text(eval('control_status_' + str(files_dict[key]["id"])),edit=True,ebg=True,bgc=[1.0,0.0,0.0],l="N")
            files_dict[key]["update"] = "N"
            
def update_button(bucket):
    global files_dict
    update_list = []
    for f in files_dict.keys():
        if files_dict[f]["update"] == "N":
            update_list.append(f)
    for i in update_list:
        oss_path_temp = files_dict[i]["oss_path"]
        path_temp = i
        def percentage(consumed_bytes,total_bytes):
            id = files_dict[path_temp]["id"]
            if total_bytes:
                rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
                cmds.progressBar(eval('control_progress_' + str(id)), edit=True, pr=rate)
        result = bucket.put_object_from_file(oss_path_temp,path_temp,progress_callback=percentage)
        if result.status == 200:
            temp_id = str(files_dict[path_temp]["id"])
            cmds.text(eval('control_status_' + temp_id),edit=True,ebg=True,bgc=[0.0,1.0,0.0],l="Y")
            id = files_dict[path_temp]["id"]
            cmds.progressBar(eval('control_progress_' + str(id)), edit=True, pr=100)

        
if __name__ == "__main__":
    global files_dict
    ID = "LTA#########9WY" # OSS accessID
    KEY = "jVc#################XagN" # OSS access key
    ENDPOINT = "oss-cn-beijing.aliyuncs.com" # OSS endpoint
    BUCKET = "yongmeng-test" #OSS bucket name
    config_dict = {"file":["cmds.getAttr('%s.fileTextureName'%node )"],  # config dict , key is the node type ,value is the func to get path attr ,notice that value is a list , in case one node with serveral path reading attrs.
                    "aiImage":["cmds.getAttr('%s.filename'%node )"],
                    "aiPhotometricLight":["cmds.getAttr('%s.aiFilename'%node )"],
                    "aiStandIn":["cmds.getAttr('%s.dso'%node )"],
                    "gpuCache":["cmds.getAttr('%s.cacheFileName'%node )"],
                    "AlembicNode":["cmds.getAttr('%s.abc_File'%node )"],
                    "reference":["cmds.referenceQuery( node,filename=True )"]}
    auth = oss2.Auth(ID, KEY)
    bucket = oss2.Bucket(auth, ENDPOINT, BUCKET)
    files_dict = all_files(config_dict)
    sort_id = []
    for key in files_dict.keys():
        sort_id.append((files_dict[key]["id"],key))
        sort_id = sorted(sort_id)
    if cmds.window('leonCheckWindow', exists=True):
        cmds.deleteUI('leonCheckWindow')
    check_window = cmds.window('leonCheckWindow',title="Leon Check Tool v1.0")
    lay_column = cmds.columnLayout( columnAttach=('both', 5), rowSpacing=10,adj=True,parent=check_window )
    first_row = cmds.rowLayout( parent=lay_column,numberOfColumns=5,ad5=2)
    cmds.text(l="id",parent=first_row,width=20)
    cmds.text(l="path",parent=first_row,width=300)
    cmds.text(l="node",parent=first_row,width=300)
    cmds.text(l="status",parent=first_row,width=50)
    cmds.text(l="upload progress",width=200,parent=first_row)
    for i in sort_id:
        temp_path_temp = i[-1]
        id = i[0]
        node = files_dict[i[-1]]["node"]
        status = files_dict[i[-1]]["status"]
        locals()['control_row_' + str(id)] = cmds.rowLayout( parent=lay_column,numberOfColumns=5,ad5=2)
        locals()['control_id_' + str(id)] = cmds.text(l="%s"%id,parent=eval('control_row_' + str(id)),width=20)
        locals()['control_path_' + str(id)] = cmds.text(l="%s"%temp_path_temp,parent=eval('control_row_' + str(id)),width=300)
        locals()['control_node_' + str(id)] = cmds.text(l="%s"%node,parent=eval('control_row_' + str(id)),width=300)
        locals()['control_status_' + str(id)] = cmds.text(l="%s"%status,parent=eval('control_row_' + str(id)),width=50)
        locals()['control_progress_' + str(id)] = cmds.progressBar(maxValue=100, width=200,parent=eval('control_row_' + str(id)))
    last_row = cmds.rowLayout( parent=lay_column,numberOfColumns=3,adj=1)
    temp = 2
    cmds.text(l="")
    cmds.button( label='Check', command='check_button(bucket)',parent=last_row,width=50 )
    cmds.button( label='Upload', command='update_button(bucket)',parent=last_row,width=50 )
    cmds.showWindow(check_window)

'''
Todo:
multi thread:check & upload
'''
