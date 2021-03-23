count=1

while [ $count -le $1 ]
do
 python send_n_qubits.py
 ((count++))
done
 
