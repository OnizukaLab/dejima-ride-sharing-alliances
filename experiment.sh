#!/usr/bin/bash

function load_rsab(){
    n=${1:-10}  # num of records for each peer's insert (default n is 10)
    start_id=1
    echo "load_rsab ${n}"
    for i in `seq 1 $provider_num`
    do
        curl -s "localhost:$((alliance_num+i+8000))/load_rsab_provider?start_id=${start_id}&record_num=${n}&step=${provider_num}" >/dev/null
        start_id=$((start_id+1))
    done
}


function set_zipf(){
    skew=${1}
    echo "set_zipf ${skew}"
    for i in `seq 0 $((alliance_num+provider_num))`
    do
        curl -s "localhost:$((i+8000))/change_val?about=zipf&theta=${skew}" >/dev/null
    done
}


function set_read_write_rate(){
    rate=${1}
    echo "set_rate ${rate}"
    for i in `seq 0 $((alliance_num+provider_num))`
    do
        curl -s "localhost:$((i+8000))/change_val?about=set_read_write_rate&rate=${rate}" >/dev/null
    done
}


function set_records_tx(){
    records_tx=${1}
    echo "set_records_tx ${records_tx}"
    for i in `seq 0 $((alliance_num+provider_num))`
    do
        curl -s "localhost:$((i+8000))/change_val?about=set_records_tx&records_tx=${records_tx}" >/dev/null
    done
}


function set_query_order(){
    on_off=${1}
    echo "set_query_order ${on_off}"
    for i in `seq 0 $((alliance_num+provider_num))`
    do
        curl -s "localhost:$((i+8000))/change_val?about=set_query_order&on_off=${on_off}" >/dev/null
    done
}


function show_lock(){
    echo "show_lock"
    for i in `seq 0 $((alliance_num+provider_num))`
    do
        curl -s "localhost:$((i+8000))/change_val?about=show_lock" >/dev/null
    done
}


function bench_rsab(){
    method=${1:-"2pl"}
    t=${2:-10}    # time (s)
    threads=1   # num of threads for each peer
    result_file="result_file"

    YmdHMS=`TZ=JST-9 date +%m%d-%H%M%S`
    mkdir -p result
    output_file=result/${result_file}_${YmdHMS}.txt
    
    echo "bench_rsab ${method} ${t}"

    (curl -s "localhost:$((8000))/rsab_alliance?bench_time=${t}&method=${method}&test_time=${test_time}" | cat >> ${output_file}) &

    # for i in `seq 1 1`
    for i in `seq 1 $alliance_num`
    do
        for j in `seq $threads`
        do
            (curl -s "localhost:$((i+8000))/rsab_alliance?bench_time=${t}&method=${method}&test_time=${test_time}" | cat >> ${output_file}) &
        done
    done

    # for i in `seq 1 2`
    for i in `seq 1 $provider_num`
    do
        for j in `seq $threads`
        do
            (curl -s "localhost:$((alliance_num+i+8000))/rsab_provider?bench_time=${t}&method=${method}&test_time=${test_time}" | cat >> ${output_file}) &
        done
    done
    
    if [ $method == "hybrid" ]; then
        sleep $((test_time+10))
    fi
    sleep ${t}
    sleep $((1+alliance_num+provider_num))

    # calculate result
    # awk '{commit+=$2} END {print commit}' ${output_file} | tee -a ${output_file}
    # awk '{commit+=$3} END {print commit}' ${output_file} | tee -a ${output_file}
    # n=$((provider_num))
    n=$((1+alliance_num+provider_num))
    sed 's/[()|, ]/ /g; s/\[s\]//g' ${output_file} | awk -v n="$n" '{cn+=$3; cn1+=$4; cn2+=$5; ct+=$6; ct1+=$7; ct2+=$8} 
        END {printf "commit:  %d (%d %d)   %.2f (%.2f %.2f)[s]\n", cn, cn1, cn2, ct/n, ct1/n, ct2/n}'
    sed 's/[()|, ]/ /g; s/\[s\]//g' ${output_file} | awk -v n="$n" '{an+=$10; an1+=$11; an2+=$12; at+=$13; at1+=$14; at2+=$15} 
        END {printf "abort:  %d (%d %d)   %.2f (%.2f %.2f)[s]\n", an, an1, an2, at/n, at1/n, at2/n}'
        
    # echo ""
        
    # sed 's/[()|, ]/ /g; s/\[s\]//g' ${output_file} | awk -v t="$t" -v n="$n" '{cn+=$3; cn1+=$4; cn2+=$5; ct+=$6; ct1+=$7; ct2+=$8} 
    #     END {printf "commit:  %.2f (%.2f %.2f)   %.2f (%.2f %.2f)[s]\n", cn/t, cn1/t, cn2/t, ct/n/t, ct1/n/t, ct2/n/t}'
    # sed 's/[()|, ]/ /g; s/\[s\]//g' ${output_file} | awk -v t="$t" -v n="$n" '{an+=$10; an1+=$11; an2+=$12; at+=$13; at1+=$14; at2+=$15} 
    #     END {printf "abort:  %.2f (%.2f %.2f)   %.2f (%.2f %.2f)[s]\n", an/t, an1/t, an2/t, at/n/t, at1/n/t, at2/n/t}'
}



alliance_num=2
provider_num=5
tx_t=1200
test_time=600

default_zipf=-1     # zipf
default_rate=80      # read-write率
default_records_tx=1    # レコード数/tx
default_query_order="off"    # txをコミットするまで次のtxに行かない

command_name=$1

function settings(){
    set_zipf $default_zipf
    set_read_write_rate $default_rate   # 0のときupdateのみ、100のときreadのみ
    set_records_tx $default_records_tx
    set_query_order $default_query_order
}

# 初期化 - 0
function batch_bench0(){
    load_rsab 10
    settings
}
if [ $command_name == "0" ]; then
    batch_bench0
fi

# 単にそれぞれの手法で実行 - 1
function batch_bench1(){
    settings
    echo -e "\n"
    bench_rsab "2pl" $tx_t
    echo ""
    bench_rsab "frs" $tx_t
    echo ""
    bench_rsab "hybrid" $tx_t
    show_lock
}
if [ $command_name == "1" ]; then
    batch_bench1
fi

# zipfの変更 - 2
function batch_bench2(){
    settings
    thetas=(0 0.2 0.4 0.6 0.8 0.99)
    for theta in "${thetas[@]}"; do
        echo -e "\n"
        set_zipf $theta
        bench_rsab "2pl" $tx_t
        echo ""
        bench_rsab "frs" $tx_t
        echo ""
    bench_rsab "hybrid" $tx_t
    done
    show_lock
}
if [ $command_name == "2" ]; then
    batch_bench2
fi

# read_write_rateの変更 - 3
function batch_bench3(){
    settings
    for ((rate = 0; rate <= 80; rate += 20)); do
        echo -e "\n"
        set_read_write_rate $rate
        bench_rsab "2pl" $tx_t
        echo ""
        bench_rsab "frs" $tx_t
        echo ""
    bench_rsab "hybrid" $tx_t
    done
    show_lock
}
if [ $command_name == "3" ]; then
    batch_bench3
fi

# records/Txの変更 - 4
function batch_bench4(){
    settings
    for ((records = 1; records <= 4; records += 1)); do
        echo -e "\n"
        set_records_tx $records
        bench_rsab "2pl" $tx_t
        echo ""
        bench_rsab "frs" $tx_t
        echo ""
    bench_rsab "hybrid" $tx_t
    done
    show_lock
}
if [ $command_name == "4" ]; then
    batch_bench4
fi

# 2次元表の元データ作成 - 5
function batch_bench5(){
    for ((records = 1; records <= 4; records += 1)); do
        default_records_tx=$records
        for (( batch_i = 1; batch_i <= 1; batch_i++ )); do
            batch_bench3
            echo -e "\n"
        done
    done
}
if [ $command_name == "5" ]; then
    batch_bench5
fi




if [ $command_name == "load_rsab" ]; then           # load_rsab 10
    load_rsab $2
elif [ $command_name == "set_zipf" ]; then          # set_zipf 0.5
    set_zipf $2
elif [ $command_name == "set_rate" ]; then          # set_rate 20
    set_read_write_rate $2
elif [ $command_name == "set_records_tx" ]; then    # set_records_tx 4
    set_records_tx $2
elif [ $command_name == "set_query_order" ]; then   # set_query_order OFF
    set_query_order $2
elif [ $command_name == "bench_rsab" ]; then        # bench_rsab frs 1200
    bench_rsab $2 $3
elif [ $command_name == "show_lock" ]; then         # show_lock
    show_lock
fi