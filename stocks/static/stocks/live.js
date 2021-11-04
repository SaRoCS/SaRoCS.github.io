document.addEventListener("DOMContentLoaded", () => {
    //get api key
    key = document.querySelector("#api-key").innerHTML;

    //when you enter a letter
    const box = document.querySelector("#symbol");
    box.addEventListener("input", (e) => {
        e = e.data;
        if(e){
            e = e.charCodeAt(0);
            if ((e >= 65 && e <= 90) || (e >= 97 && e <= 122)){
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
                                        let option = document.createElement('option');//document.querySelector(`#o${i}`)
                                        let temp = `${data[i]['symbol']}: ${data[i]['name']}`
                                        option.value = temp;
                                        list.appendChild(option);
                                    }
                                    else if (res2 !== null) {
                                        let option = document.createElement('option');//document.querySelector(`#o${i}`)
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
            }
        }
    });

});