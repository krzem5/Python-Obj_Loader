import os


ml={}
for fp in os.listdir("."):
	if (fp[-4:]==".mtl"):
		with open(fp,"r") as f:
			t=None
			for k in [e.strip().split(" ") for e in f.read().split("\n") if len(e.strip())>0 and e.strip()[0]!="#"]:
				if (k[0]=="newmtl"):
					if (k[1] not in list(ml.keys())):
						ml[k[1]]={}
						t=k[1]
					else:
						t=1
				else:
					if (t==1):
						continue
					if (t==None):
						raise RuntimeError("AAA")
					ml[t][k[0]]=k[1:]
		os.remove(fp)
	elif (fp[-4:]==".obj"):
		with open(fp,"r") as f:
			dt=[(e.strip() if e.strip().split(" ")[0]!="mtllib" else "mtllib material.mtl") for e in f.read().split("\n") if len(e.strip())>0 and e.strip()[0]!="#"]
		with open(fp,"w") as f:
			f.write("\n".join(dt))
for k in ml.keys():
	ml[k]={k:v for k,v in sorted(ml[k].items(),key=lambda e:e[0])}
ml={k:v for k,v in sorted(ml.items(),key=lambda e:e[0])}
with open("material.mtl","w") as f:
	for k in ml.keys():
		f.write(f"newmtl {k}\n")
		for e in ml[k].items():
			f.write(f"{e[0]} {' '.join(e[1])}\n")
