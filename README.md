===========
Pyzview
===========

Requirements
------------

You'll need to install ziew stanalon app, You can grab it from:


``https://github.com/ohadmen/zview/releases/latest``

Installation
------------
    pip install pyzview


Usage example
-------------
    from pyzview import Pyzview

    import numpy as np
    
    zv = Pyzview()

    n = 400

    pts = np.ones((n,6))*np.nan

    zv.remove_shape(-1)

    i=0

    while True:

        pts[i%n]=np.cos(np.array([15,13,11,7,2,1])*i*0.005/np.pi)**2

        i=i+1
        
        k = zv.add_points("demo", pts) if 'k' not in locals() else zv.update_points(k, pts)
