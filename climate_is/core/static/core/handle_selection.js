function showOnPick(){
    const aggrSelect = document.getElementById('aggregate-select')
    // что-то мне подсказывает, что это фигня какая-то ...
    const temp_options = document.querySelectorAll('.temp-option');
    const precip_options = document.querySelectorAll('.precip-option');

    precip_options.forEach(option => {
        option.style.display = 'none';
    });
    temp_options.forEach(option => {
        option.style.display = 'none';
    });
    
    // TO-DO!! эта штука подразумевает, что id температуры всегда 1
    // надо добавить какие-нибудь aliasы? кодовые слова?
    // ну не могу же я каждый раз делать fetch на api чтобы узнать айдишник осдков...
    // если выбрана температура, то + cdd и hdd
    if (this.value === '1') {
        temp_options.forEach(option => {
            option.style.display = 'block';
        });
    }else if (this.value === '4'){      // пххххххахахахаааа
        precip_options.forEach(option => {
            option.style.display = 'block';
        });       
    }
    
    aggrSelect.value = 'avg';
}

document.addEventListener('DOMContentLoaded', function(){
    const paramSelect = document.getElementById('parameter-select');
    //const temp_options = document.querySelectorAll('.temp-option');
    paramSelect.addEventListener('change', showOnPick)
});