#!/bin/bash
# Acquire a run of frames using a single camera

if [ $# -eq 0 ]; then
   echo "Specify a camera!"
   exit 1
fi

cam=$1 
basedir=/tmp/saft-acquire-
exp_count=1
exp_start=0
exp_time=10
exp_shutter_close=0
solve_wcs=0

# How much do we trust the telescope pointing (in degrees)?
pointing_uncertainty=0.5

if [[ (${exp_shutter_close} -eq 1) ]]; then
  setINDI ${cam}.shutter.close="On"
  setINDI ${cam}.shutter.auto="Off"
else
  setINDI ${cam}.shutter.auto="On"
fi

setINDI ${cam}.image_exposure.time=${exp_time}
setINDI ${cam}.archive.base_name=${basedir}
#setINDI ${cam}.image.number=${exp_start}
setINDI ${cam}.acquire.single=On


setINDI ${cam}.fits_script.file="getshm && frameheader"
setINDI ${cam}.fits_script.run=On

setINDI ${cam}.image_binning.x=2
setINDI ${cam}.image_binning.y=2

setINDI ${cam}.image_region_control.option=Off
setINDI ${cam}.image_region.x=768
setINDI ${cam}.image_region.y=768
setINDI ${cam}.image_region.w=512
setINDI ${cam}.image_region.h=512

for i in `seq 1 1 ${exp_count}`; do
    setINDI ${cam}.sequence.run=On
    echo "start"

    sleep 1
    run=1
    while [[ (${run} -eq 1) ]]; do
        sleep 1
        run=`getINDI ${cam}.sequence.run | cut -f 2,2 -d "=" | grep -c "On"`
    done
    saved=`getINDI ${cam}.file.name | cut -f 2,2 -d "="`
	
	if [[ (${solve_wcs} -eq 1) ]]; then
		solvedname="$(basename ${saved} .fits).solved.fits"
		wcsname="$(basename ${saved} .fits).wcs"
#		ra=$(tsreduce metadata ${saved} | grep RAEOD | cut -d' ' -f3)
#		dec=$(tsreduce metadata ${saved} | grep DECEOD | cut -d' ' -f3)
#		echo $FILENAME $RA $DEC $SOLVEDNAME $WCSNAME

                /usr/local/astrometry/bin/solve-field --no-fits2fits --overwrite --no-plots --axy "none" --rdls "none" --match "none" --corr "none" --index-xyls "none" --solved "none" --new-fits ${solvedname} --scale-units "arcminwidth" --scale-high 13.4 ${saved}
#		/usr/local/astrometry/bin/solve-field --no-fits2fits --overwrite --no-plots --axy "none" --rdls "none" --match "none" --corr "none" --index-xyls "none" --solved "none" --new-fits ${solvedname} --scale-units "arcminwidth" --scale-high 13.4 --ra ${ra} --dec ${dec} --radius ${pointing_uncertainty} ${saved}
		rm "${wcsname}"
		
		if [[ (-e ${solvedname}) ]]; then
	    	tsreduce preview ${solvedname} Online_Preview
		else
			echo "Failed to solve WCS for" ${saved}
	    		/home/saft/src/tsreduce/tsreduce preview ${saved} Online_Preview
		fi
	else
    	# /home/saft/src/tsreduce/tsreduce preview ${saved} Online_Preview
	echo Created new FITS file
	fi
    echo "Saved " ${saved}
done
