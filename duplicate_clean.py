#coding=utf-8
import sys
import os
import re
import filecmp
import itertools
import hashlib

exclude_re = re.compile(r"[.#@]+.+")
exclude_dir = {
    'tobe_del',
}

trash_path = None
def remove_func(filepath):
    # os.remove(filepath)
    try:
        n = os.path.basename(filepath)
        dst = os.path.join(trash_path,n)
        print "dst=",dst
        os.rename(filepath,dst)
    except Exception as e:
        print "exception:{} when delfile={}".format(e,filepath)



def need_search(dir_name):
    if exclude_re.match(dir_name):
        print 'ignore by re:',dir_name 
        return False
    if dir_name in exclude_dir:
        print 'ignore by exclude:',dir_name
        return False
    return True

def file_md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def strip(move_dst,*args):
    min_ct = None
    min_f = None
    for f in args:
        if min_ct is None or f.ct < min_f:
            min_f = f

    if min_f:
        print 'ct={} left file={} '.format(min_f.ct,min_f.fp)
        for f in args:
            if f is not min_f:
                print 'ct={} delfile={} '.format(f.ct,f.fp)
                remove_func(f.fp)

class finfo(object):
    __dict_size = dict()

    def __init__(self,fullpath):
        self.fp = fullpath
        stat = os.stat(fullpath)
        self.ct = stat.st_ctime
        self.size = stat.st_size
        self.md5 = None


    def __eq__(self,other):
        return self.size == other.size and filecmp.cmp(self.fp,other.fp)

    def __repr__(self):
        return 'file={},size={},ct={}'.format(self.fp,self.size,self.ct)

    @classmethod
    def add(cls,fullpath):
        fi = finfo(fullpath)
        l = cls.__dict_size.setdefault(fi.size,list())
        l.append(fi)

    @classmethod
    def check_same(cls,finfo_list):
        if len(finfo_list) < 2:
            return

        if len(finfo_list) == 2:
            f1 = finfo_list[0]
            f2 = finfo_list[1]
            if filecmp.cmp(f1.fp,f2.fp):
                print 'same_file=2 by cmp size={}'.format(f1.size)
                strip(cls.__dst_folder, f1,f2)       
            return
        
        dict_md5 = {}
        for f in finfo_list:
            f.md5 = file_md5(f.fp)
            l = dict_md5.setdefault(f.md5,[])
            l.append(f)

        for k,v in dict_md5.iteritems():
            if len(v) > 1:
                print 'same_file={} by md5 {} size={}'.format(len(v),k,v[0].size)
                strip(cls.__dst_folder, *v)

    @classmethod
    def clean(cls,dst_folder):
        cls.__dst_folder = dst_folder
        for k,v in cls.__dict_size.iteritems():
            # print 'check size={}'.format(k)
            cls.check_same(v)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage:\npython.py duplicate_clean /volume2/photo"
        exit(0)

    rootdir = sys.argv[1]

    for parent,dirs,filenames in os.walk(rootdir,topdown=True):    #三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
        dirs[:] = [d for d in dirs if need_search(d)]
        for dirname in dirs:                       #输出文件夹信息
            #print("parent is:" + parent)
            #print("dirname is:" + dirname)
            #print("the full name of the file is:" + os.path.join(parent, dirname))  # 输出文件夹路径信息
            print("folder:",os.path.join(parent, dirname))  # 输出文件夹路径信息


        for filename in filenames:  # 输出文件信息
            fullpath = os.path.join(parent, filename)
            #print("parent is:" + parent)
            # print("filename is:" + filename)
            # print("fullpath is:" + fullpath)
            # print dir(stat)
            # print "time=",stat.st_atime,stat.st_mtime,stat.st_ctime
            # print "size=",stat.st_size
            finfo.add(fullpath)

    trash_path = os.path.join(rootdir,"tobe_del")
    if not os.path.exists(trash_path):
        os.makedirs(trash_path)
    finfo.clean(rootdir)