from setuptools import setup, find_packages, Extension

module = Extension("zview_module",
                       sources=["pyzview/zview_inf.cpp"],
                       libraries = ["zview_inf"],   
                       
              )

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()
setup(
     name='pyzview',  
     version='1.48a',
     author="Ohad Menashe",
     author_email="ohad.men@gmail.com",
     description="zview python inferface",
     long_description=long_description,
     url="https://github.com/ohadmen/pyzview",
     packages=find_packages(),
     ext_modules=[module],
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )