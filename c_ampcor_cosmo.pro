pro c_ampcor_cosmo,id1,id2,nproc=nproc

print
print,'%% create_ampcor.pro'
print,'%% Create the bat file to run ampcor'
print

close,/all

print,'Id1 : ',id1
print,'Id2 : ',id2
print

id=id1+'-'+id2

po = load_off_param(id+'.par')
xoff=po.r0
yoff=po.z0
print,'Offset :',xoff,yoff

p1 = load_isp_param(id1+'.par')
p2 = load_isp_param(id2+'.par')

nl=max([p1.nrec,p2.nrec])
if not keyword_set(nproc) then nproc=14

x_start=1L
x_end=p1.npix

y_start=0L+max([0,fix(-po.z0/30L+1.5)*30L])
y_end=nl 

nrec=0L+y_end-y_start

bat_id='bat_'+id1+'-'+id2
y_slope=(p1.azsp-p2.azsp)/p1.azsp
print,'Reference Azimuth Res:',p1.azsp
print,'Secondary Azimuth Res:',p2.azsp
print,'Computed yslope: ', y_slope
print,'Number of record of ref. SLC :',nrec

print,'Divide offsets into ',nproc,' chunks ..'

rgspac=30L
line_spac=30L

nn=long(nrec/line_spac/nproc+0.5)
print,'Number of offset lines per chunk :',nn

numb=strcompress(indgen(200)+1,/r)
numb=numb[0:nproc-1]

y_curr=long(y_start)

print,'Bat file :',bat_id
openw,2,bat_id

for i=1,nproc do begin
openw,1,id+'.offmap_'+numb(i-1)+'.in'
printf,1,id1+'.slc'
printf,1,id2+'.slc'
printf,1,id+'.offmap'+'_'+numb(i-1)
printf,2,'./ampcor_large '+id+'.offmap'+'_'+numb(i-1)+'.in old &'
printf,1,p1.npix,p2.npix,format='(i5,1x,i5)'
printf,1,(y_curr-2*line_spac)>0,y_curr+line_spac*(nn-1L),line_spac,format='(i6,1x,i8,1x,i3)'
printf,1,x_start,x_end,rgspac,format='(i4,1x,i5,1x,i5)'
printf,1,'64 64'
printf,1,'32 32'
printf,1,'1 1'
xoff0=xoff & yoff0=fix(yoff+y_slope*(2.*y_curr+line_spac*(nn-1))/2.+0.5)
if (i eq 1 or i eq nproc) then print,yoff0
if (i eq 1 or i eq nproc) then print,y_curr
if (i eq 1 or i eq nproc) then print,y_slope
if (i eq 1 or i eq nproc) then print,line_spac
printf,1,xoff0,yoff0,format='(i5,1x,i6)'
printf,1,'0. 1.e10'
printf,1,'f f'
close,1
print,id+'.offmap_'+numb(i-1)+'.in',y_curr,y_curr+line_spac*(nn-1L)
y_curr=y_curr+long(line_spac*nn)
endfor

spawn,'chmod 777 '+bat_id
close,2

;endfor

fin:
end
