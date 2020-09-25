import os
import struct
import math
import panda3d.core



STRIDE=8



def _write_poses(f,cl,ol,pl):
	def _name(nm):
		return nm.split(" ")[-1][:-len(nm.split("::")[-1])-2]
	def _join(l,ch,k):
		if (k in list(ch.keys())):
			if ("children" not in list(l[k].keys())):
				l[k]["children"]=[]
			for e in ch[k]:
				l=_join(l,ch,e)
				l[k]["children"]+=[l[e]]
				del l[e]
		return l
	def _read_mdl(cl,ol,l,ch,nr,k,anr,bi):
		print(" "*bi+f"Reading Model '{k['name']}'...")
		if (_name(k["name"]) not in list(l.keys())):
			l[_name(k["name"])]={}
		l[_name(k["name"])]["dx"],l[_name(k["name"])]["dy"],l[_name(k["name"])]["dz"]=_get_prop70(_get_child(k,"Properties70"),"Lcl Translation")
		l[_name(k["name"])]["name"]=k["name"]
		g=[[],[],[],[],[],[],[]]
		m=None
		if (anr==True):
			nr+=[_name(k["name"])]
		print(" "*bi+"Reading Children...")
		for et,e in _get_refs(cl,ol,k["id"],-1):
			if (e["type"]=="NodeAttribute"):
				print(" "*bi+"Parsing Attributes...")
				l[_name(k["name"])]["len"]=_get_prop70(_get_child(e,"Properties70"),"Size")[0]
			elif (e["type"]=="Model"):
				if (_name(k["name"]) not in list(ch.keys())):
					ch[_name(k["name"])]=[e["name"][:-len(e["name"].split("::")[-1])-2]]
				elif (e["name"][:-len(e["name"].split("::")[-1])-2] not in ch[_name(k["name"])]):
					ch[_name(k["name"])]+=[e["name"][:-len(e["name"].split("::")[-1])-2]]
				l,ch,nr,tg,tm=_read_mdl(cl,ol,l,ch,nr,e,True,bi+2)
				if (tm!=None and m!=None):
					raise RuntimeError("Duplicate Material!")
				print(" "*bi+"Merging Data...")
				if (tm!=None):
					m=tm
				for i,j in enumerate(tg):
					g[i]+=j
			elif (e["type"]=="Geometry"):
				print(" "*bi+"Parsing Geometry...")
				vl=_get_child(e,"Vertices")["data"][0]
				nl=_get_child(_get_child(e,"LayerElementNormal"),"Normals")["data"][0]
				uvl=_get_child(_get_child(e,"LayerElementUV"),"UV")["data"][0]
				uvil=_get_child(_get_child(e,"LayerElementUV"),"UVIndex")["data"][0]
				il_=_get_child(e,"PolygonVertexIndex")["data"][0]
				i=0
				c=[]
				il=[]
				print(" "*bi+"Triangulating Polygons...")
				while (i<len(il_)):
					if (il_[i]<0):
						c+=[(~il_[i],i+0)]
						if (len(c)==3):
							il+=c
						else:
							tc=panda3d.core.Triangulator3()
							lvl=[]
							for n in c:
								lvl+=[n]
								tc.addPolygonVertex(tc.addVertex(*vl[n[0]*3:n[0]*3+3]))
							tc.triangulate()
							for n in range(0,tc.getNumTriangles()):
								il+=[lvl[tc.getTriangleV0(n)],lvl[tc.getTriangleV1(n)],lvl[tc.getTriangleV2(n)]]
						c=[]
					else:
						c+=[(il_[i],i+0)]
					i+=1
				print(" "*bi+"Merging Data...")
				g[0]+=vl
				g[1]+=nl
				g[2]+=uvl
				g[3]+=[(se[0]+(len(g[0])-len(vl))//3,se[1]+(len(g[1])-len(nl))) for se in il]
				g[4]+=[se+(len(g[2])-len(uvl))//3 for se in uvil]
				g[5]+=[e]
				g[6]+=[(len(g[3]),_get_child(_get_child(e,"LayerElementNormal"),"MappingInformationType")["data"][0])]
			elif (e["type"]=="Material"):
				print(" "*bi+"Parsing Material...")
				if (m!=None):
					raise RuntimeError("Duplicate Material!")
				print(" "*bi+"Merging Data...")
				m={"c":{"a":_get_prop70(_get_child(e,"Properties70"),"AmbientColor"),"d":_get_prop70(_get_child(e,"Properties70"),"DiffuseColor"),"s":_get_prop70(_get_child(e,"Properties70"),"SpecularColor")},"df":_get_prop70(_get_child(e,"Properties70"),"DiffuseFactor")[0],"se":_get_prop70(_get_child(e,"Properties70"),"ShininessExponent")[0],"d":_get_prop70(_get_child(e,"Properties70"),"Diffuse"),"s":_get_prop70(_get_child(e,"Properties70"),"Specular")}
			elif (e["type"]=="AnimationCurveNode"):
				print(" "*bi+"Parsing Default Offsets...")
				if (et=="Lcl Translation"):
					l[_name(k["name"])]["dx"]=_get_prop70(_get_child(e,"Properties70"),"d|X")[0]
					l[_name(k["name"])]["dy"]=_get_prop70(_get_child(e,"Properties70"),"d|Y")[0]
					l[_name(k["name"])]["dz"]=_get_prop70(_get_child(e,"Properties70"),"d|Z")[0]
				elif (et=="Lcl Rotation"):
					l[_name(k["name"])]["drx"]=_get_prop70(_get_child(e,"Properties70"),"d|X")[0]
					l[_name(k["name"])]["dry"]=_get_prop70(_get_child(e,"Properties70"),"d|Y")[0]
					l[_name(k["name"])]["drz"]=_get_prop70(_get_child(e,"Properties70"),"d|Z")[0]
				else:
					raise RuntimeError(et)
			else:
				raise RuntimeError(e["type"])
		return (l,ch,nr,g,m)
	def _read_deform(cl,ol,l,k,i):
		print(" "*i+f"Parsing Deform '{k['name']}'...")
		l[_name(k["name"])]["deform"]={"data":([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1] if _get_child(k,"Transform")==None else _get_child(k,"Transform")["data"][0]),**({"indexes":_get_child(k,"Indexes")["data"][0],"weights":_get_child(k,"Weights")["data"][0]} if _get_child(k,"Indexes")!=None else {"indexes":[],"weights":[]})}
		if (k["id"] in list(cl.keys())):
			for _,e in _get_refs(cl,ol,k["id"],-1):
				if (e["type"]=="Deformer"):
					l=_read_deform(cl,ol,l,e,i+2)
				elif (e["type"]=="Model"):
					continue
				else:
					raise RuntimeError(e["type"])
		return l
	def _write_mdl(f,k,i):
		print(" "*i+f"Writing Model '{k['name']}' to File...")
		if ("children" not in list(k.keys())):
			k["children"]=[]
		if ("deform" not in list(k.keys())):
			k["deform"]={"data":[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],"indexes":[],"weights":[]}
		if ("dx" not in list(k.keys())):
			k["dx"]=0
			k["dy"]=0
			k["dz"]=0
		if ("drx" not in list(k.keys())):
			k["drx"]=0
			k["dry"]=0
			k["drz"]=0
		if ("mat" not in list(k.keys())):
			k["mat"]=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
		k["mat"]=[k["mat"][0],k["mat"][4],k["mat"][8],k["mat"][12],k["mat"][1],k["mat"][5],k["mat"][9],k["mat"][13],k["mat"][2],k["mat"][6],k["mat"][10],k["mat"][14],k["mat"][3],k["mat"][7],k["mat"][11],k["mat"][15]]
		nm=_name(k["name"])
		f.write(struct.pack(f">B{len(nm[:255])}sfB38fI{len(k['deform']['indexes'])}H{len(k['deform']['indexes'])}f",len(nm[:255]),bytes(nm[:255],"utf-8"),k["len"],len(k["children"]),k["dx"],k["dy"],k["dz"],k["drx"],k["dry"],k["drz"],*k["mat"],*k["deform"]["data"],len(k["deform"]["indexes"]),*k["deform"]["indexes"],*k["deform"]["weights"]))
		for e in k["children"]:
			_write_mdl(f,e,i+2)
	print("Parsing Poses...")
	f.write(struct.pack(">B",len(pl)))
	for p in pl:
		print(f"  Parsing Pose '{p['name']}'...")
		l={}
		ch={}
		nr=[]
		g=[[],[],[],[],[],[],[]]
		m=None
		print("    Parsing Nodes...")
		for ok in p["children"]:
			if (ok["name"]=="PoseNode"):
				k=ol[_get_child(ok,"Node")["data"][0]]
				if (k["type"]=="NodeAttribute"):
					print(f"      Parsing Node Attribute '{k['name']}'...")
					if (_name(k["name"]) not in list(l.keys())):
						l[_name(k["name"])]={}
					print("      Merging Data...")
					l[_name(k["name"])]["len"]=_get_prop70(_get_child(k,"Properties70"),"Size")[0]
				elif (k["type"]=="Model"):
					l,ch,nr,tg,tm=_read_mdl(cl,ol,l,ch,nr,k,False,6)
					if (tm!=None and m!=None):
						raise RuntimeError("Duplicate Material!")
					if (tm!=None):
						m=tm
					print("      Merging Data...")
					l[_name(k["name"])]["mat"]=_get_child(ok,"Matrix")["data"][0]
					for i,j in enumerate(tg):
						g[i]+=j
				else:
					raise RuntimeError(k["type"])
		print("    Parsing Deforms...")
		for k in g[5]:
			for _,e in _get_refs(cl,ol,k["id"],-1):
				l=_read_deform(cl,ol,l,e,6)
		print("    Creating Model Tree...")
		for k in [e for e in l.keys() if e not in nr]:
			l=_join(l,ch,k)
		l={k:v for k,v in l.items() if "len" in list(v.keys())}
		print("    Preprocessing Verticies...")
		dtl=[]
		il=[]
		vhl=[]
		lp=-1
		for i,k in enumerate(g[3]):
			if (i*100//len(g[3])>lp):
				print(f"      {i*100//len(g[3])}% Complete ({len(dtl)//STRIDE}v, {len(il)//3}i)...")
				lp=i*100//len(g[3])
			n=None
			for e in g[6]:
				if (i<=e[0]):
					if (e[1]=="ByPolygonVertex"):
						n=g[1][k[1]*3:k[1]*3+3]
					elif (e[1]=="ByVertice"):
						n=g[1][k[0]*3:k[0]*3+3]
			v=(*g[0][k[0]*3:k[0]*3+3],*n,*g[2][g[4][k[1]]*2:g[4][k[1]]*2+2])
			if (len(v)!=STRIDE):
				raise RuntimeError(str(v))
			if (hash(v) not in vhl):
				dtl+=v
				vhl+=[hash(v)]
			il+=[vhl.index(hash(v))]
		print(f"      100% Complete ({len(dtl)//STRIDE}v, {len(il)//3}i)...\n    Writing To File...")
		nm=_name(p["name"])
		f.write(struct.pack(f">B{len(nm)}sBII{len(dtl)+17}f{len(il)}H",len(nm),bytes(nm,"utf-8"),len(list(l.keys())),len(dtl)//STRIDE,len(il),*m["c"]["a"],*m["c"]["d"],*m["c"]["s"],m["df"],m["se"],*m["d"],*m["s"],*dtl,*il))
		print("    Writing Models To File...")
		for k in l.values():
			_write_mdl(f,k,6)



for fp in os.listdir("."):
	if (fp[-4:]==".obj"):
		with open(fp,"rb") as f:
			dt=f.read()
		print(fp)
		gs=None
		ol=None
		cl=None
		df=None
		as_=None
		pl=[]
		while (i<len(dt)):
			i,e=_parse(dt,i)
			if (i==None):
				break
			if (e["name"]=="GlobalSettings"):
				gs=e
			elif (e["name"]=="Objects"):
				ol={}
				for k in e["children"]:
					ol[k["data"][0]]={"id":k["data"][0],"type":k["name"],"name":k["data"][1],"children":k["children"]}
					if (k["name"]=="AnimationStack"):
						as_=k["data"][0]
					if (k["name"]=="Pose"):
						pl+=[ol[k["data"][0]]]
			elif (e["name"]=="Definitions"):
				df={}
				for k in e["children"]:
					if (k["name"]=="ObjectType" and k["data"][0]!="GlobalSettings"):
						if (_get_child(k,"PropertyTemplate")!=None):
							df[k["data"][0]]=_get_child(_get_child(k,"PropertyTemplate"),"Properties70")["children"]
						else:
							df[k["data"][0]]=[]
			elif (e["name"]=="Connections"):
				cl={}
				for c in e["children"]:
					if (c["data"][2] not in list(cl.keys())):
						cl[c["data"][2]]=[]
					cl[c["data"][2]]+=[[c["data"][1],(None if len(c["data"])==3 else c["data"][3])]]
		for k,v in ol.items():
			ch=_get_child(v,"Properties70")
			kn=[]
			if (ch==None):
				v["children"]+=[{"name":"Properties70","children":[]}]
				ch=v["children"][-1]
			else:
				for e in ch["children"]:
					kn+=[e["data"][0]]
			for e in df[v["type"]]:
				if (e["data"][0] not in kn):
					kn+=[e["data"][0]]
					ch["children"]+=[e]
		off=([_get_prop70(_get_child(gs,"Properties70"),"TimeSpanStart")[0],_get_prop70(_get_child(gs,"Properties70"),"TimeSpanStop")[0]] if as_==None else [_get_prop70(_get_child(ol[as_],"Properties70"),"LocalStart")[0],_get_prop70(_get_child(ol[as_],"Properties70"),"LocalStop")[0]])
		off[1]=_get_frame(off,off[1])
		if (as_!=None):
			with open(f"{fp[:-4]}.anm","wb") as f:
				f.write(struct.pack(">H",off[1]+1))
				_write_anim(f,off,cl,ol,_get_refs(cl,ol,0))
		if (len(pl)>0):
			with open(f"{fp[:-4]}.mdl","wb") as f:
				_write_poses(f,cl,ol,pl)
