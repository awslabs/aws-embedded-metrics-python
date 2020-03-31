# main functionality

import numpy as him
array=him.array([[0,1,2,3],[2,5,8,9],[4,5,7,96]],dtype='int')
print(array)
b = him.array((2, 3, 2,52,22)) 
print(b)
c=him.zeros((2,2))
print(c)
d=array.T
print(d)
e= him.full((10, 4), 60, dtype = 'complex') 
print(e)
f= him.random.random((10,4)) 
print(f)
g= him.arange(0, 100, 3) 
print(g)
h=him.linspace(0,90,5)
print(h)
arr = him.array([[1, 2, 3], [4, 5, 6]]) 
flarr = arr.flatten()
print(flarr) 
arr = him.array([[-1, 2, 0, 4], 
                [4, 5, 6, 0], 
                [2, 0, 7, 8], 
                [3, -7, 4, 2]]) 
kol=arr[0:4:2]
print(kol)
b = him.array((1 , 3, 2,0,0)) 
kol=b[:-2]
print(kol)
condition=arr!=0
jmm=arr[condition]
print(jmm)
print(b==2)
arr = him.array([[1, 5, 6], 
                [4, 7, 2], 
                [3, 1, 9]]) 
print(arr.min(axis=0))
print(arr.sum())
print(arr.cumsum(axis=1))
kam=him.array([1,2,3,4,5,6,5])
print(him.sqrt(kam))
print(him.sort(kam,axis=0,kind='mergesort'))
