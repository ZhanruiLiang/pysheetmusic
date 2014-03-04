name=$1
if [[ -n $2 ]];
then
    tmp=$2.zip
else
    tmp=/tmp/sheet-$1.zip
fi
cp $1 $tmp
vim $tmp
rm $tmp
