document.addEventListener("DOMContentLoaded", () => {
    //get api key
    key = document.querySelector("#api-key").innerHTML;

    //when you enter a letter
    const box = document.querySelector("#symbol");
    box.addEventListener("keyup", (e) => {
        if ((e['keyCode'] >= 65 && e['keyCode'] <= 90) || (e['keyCode'] >= 97 && e['keyCode'] <= 122)){
            let symbol = box.value;
            //if letters api calls
            if (symbol !== ''){
                Promise.all([
                    fetch(`https://financialmodelingprep.com/api/v3/search?query=${symbol}&exchange=NYSE&limit=5&apikey=${key}`),
                    fetch(`https://financialmodelingprep.com/api/v3/search?query=${symbol}&exchange=NASDAQ&limit=5&apikey=${key}`)
                ])
                .then(responses => {
                    return Promise.all(responses.map(function (response) {
                        return response.json();
                    }));
                })
                .then( data => {
                    //combine responses
                    data = data[0].concat(data[1]);
                    if (data !== undefined){
                        //populate options
                        let list = document.querySelector("#options");
                        list.innerHTML = '';
                        for (i = 0; i < data.length; i++) {
                            
                            if (data[i]['name'] !== null) {
                                //filter out duplicates
                                let patt = /-A$/;
                                let patt2 = /-B$/;
                                let res = data[i]['symbol'].match(patt);
                                let res2 = data[i]['symbol'].match(patt2)
                                
                                if (res === null && res2 === null) {
                                    let option = document.createElement('option');
                                    let temp = `${data[i]['symbol']}: ${data[i]['name']}`
                                    option.value = temp;
                                    list.appendChild(option);
                                }
                                else if (res2 !== null) {
                                    let option = document.createElement('option');
                                    let symbol = data[i]['symbol'].substring(0, data[i]['symbol'].length - 2);
                                    let temp = `${symbol}: ${data[i]['name']}`
                                    option.value = temp;
                                    list.appendChild(option);
                                }
                            }
                        };
                    };
                });
                
            };
        };
    });

});