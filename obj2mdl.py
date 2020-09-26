import os
import struct



for fp in os.listdir("."):
	if (fp[-4:]==".obj"):
		with open(fp,"r") as f:
			dt=f.read().replace("\r","").split("\n")
		mtl={}
		vl=[]
		nl=[]
		uvl=[]
		ll={}
		cl=None
		cg=None
		for e in dt:
			if (len(e.strip())>0):
				e=e.strip().split(" ")
				if (e[0][0]=="#"):
					continue
				elif (e[0]=="mtllib"):
					with open(e[1],"r") as f:
						mdt=f.read().replace("\r","").split("\n")
					cm=None
					for me in mdt:
						if (len(me.strip())>0):
							me=me.strip().split(" ")
							if (me[0][0]=="#"):
								continue
							elif (me[0]=="newmtl"):
								if (me[1] in list(mtl.keys())):
									raise RuntimeError
								cm=me[1]
								mtl[cm]={"ac":[0,0,0],"dc":[0,0,0],"sc":[0,0,0],"se":0,"_r":False}
							elif (me[0]=="Ka"):
								mtl[cm]["ac"]=[float(me[1]),float(me[2]),float(me[3])]
							elif (me[0]=="Kd"):
								mtl[cm]["dc"]=[float(me[1]),float(me[2]),float(me[3])]
							elif (me[0]=="Ks"):
								mtl[cm]["sc"]=[float(me[1]),float(me[2]),float(me[3])]
							elif (me[0]=="Ns"):
								mtl[cm]["se"]=float(me[1])
							else:
								raise RuntimeError(me)
				elif (e[0]=="g"):
					cg=e[1]
				elif (e[0]=="v"):
					vl+=[(float(e[1]),float(e[2]),float(e[3]))]
				elif (e[0]=="vn"):
					nl+=[(float(e[1]),float(e[2]),float(e[3]))]
				elif (e[0]=="vt"):
					uvl+=[(float(e[1]),float(e[2]))]
				elif (e[0]=="usemtl"):
					cl=e[1]
					if (cl not in list(ll.keys())):
						ll[cl]={"mtl":mtl[e[1]],"g":{},"il":[],"dtl":[],"vhl":[]}
					if (cg!=None and cg not in list(ll[cl]["g"].keys())):
						ll[cl]["g"][cg]=[]
				elif (e[0]=="f"):
					if (len(e[1:])!=3):
						raise RuntimeError(len(e[1:]))
					for k in e[1:]:
						k=k.split("/")
						k=[int(k[0])-1,int(k[1])-1,int(k[2])-1]
						v=(*vl[k[0]],*nl[k[2]],*uvl[k[1]])
						if (hash(v) not in ll[cl]["vhl"]):
							ll[cl]["dtl"]+=v
							ll[cl]["vhl"]+=[hash(v)]
						ll[cl]["g"][cg]+=[ll[cl]["vhl"].index(hash(v))]
						ll[cl]["il"]+=[ll[cl]["vhl"].index(hash(v))]
				else:
					raise RuntimeError(e)
		with open(f"{fp[:-4]}.mdl","wb") as f:
			f.write(struct.pack("<B",len(list(ll.keys()))))
			for k,v in ll.items():
				f.write(struct.pack(f"<B{len(k[:255])}sBII{len(v['dtl'])+10}f{len(v['il'])}H",len(k[:255]),bytes(k[:255],"utf-8"),len(list(v["g"].keys())),len(v["dtl"])//8,len(v["il"]),*v["mtl"]["ac"],*v["mtl"]["dc"],*v["mtl"]["sc"],v["mtl"]["se"],*v["dtl"],*v["il"]))
				for k,e in v["g"].items():
					f.write(struct.pack(f"<B{len(k[:255])}sfB6fI{len(e)}H{len(e)}f",len(k[:255]),bytes(k[:255],"utf-8"),1,0,0,0,0,0,0,0,len(e),*e,*((1,)*len(e))))
