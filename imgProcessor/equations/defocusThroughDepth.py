from __future__ import division


def defocusThroughDepth(u, uf, f, fn, k=2.355):
    '''
    return the defocus (mm std) through DOF
    
    u -> scene point (depth value)
    uf -> in-focus position (the distance at which the scene point should be placed in order to be focused)
    f -> focal length
    k -> camera dependent constant (transferring blur circle to PSF), 2.335 would be FHWD of 2dgaussian
    fn --> f-number (relative aperture)  
     
    equation (3) taken from http://linkinghub.elsevier.com/retrieve/pii/S0031320312004736
        Pertuz et.al. "Analysis of focus measure operators for shape-from-focus"
        
    all parameter should be in same physical unit [mm]
    
    !! assumes spatial invariant blur
    '''
    # A = f/fn 
    return (k/fn) * (f**2*abs(u-uf)) / (u*(uf-f)) 
    
    

