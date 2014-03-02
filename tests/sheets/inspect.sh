name=$1
tmp=/tmp/sheet-$1.zip
cp $1 $tmp
vim $tmp
rm $tmp
