document.addEventListener("DOMContentLoaded", () => {

    const graph = document.querySelector("#graph")

    let symbol = document.querySelector("#title").innerHTML.match(/\(([^)]+)\)/)[1];

    getHTML(`/graph/${symbol}`, (response) => {
        //append graph
        appendGraph(response);
        //set titles
        document.querySelector(".g-xtitle").firstElementChild.innerHTML = "Date";
        document.querySelector(".g-ytitle").firstElementChild.innerHTML = "Closing Prices";

        //get elements
        const svg = graph.querySelector("svg");
        let original = svg.querySelector(".js-line").getAttribute('d');

        //check the graph
        check(original, svg);

        //interval to check if graph has changed
        setInterval(() => {
            let d = svg.querySelector(".js-line").getAttribute('d');
            //if it has changed update color
            if (d !== original || svg.querySelector(".js-line").style.stroke === "rgb(211, 211, 211)") {
                check(d, svg);
                original = d;
            }
        }, 50);
    });

    function check(d, svg) {
        //separate svg path into coordinates
        d = d.split("L");
        d.shift()
        if (d !== undefined) {
            let coords = [];

            for (i = 0; i < d.length; i++) {
                let numbers = d[i];
                let numArray = numbers.split(",");

                let coordinate = {
                    x: parseFloat(numArray[0]),
                    y: parseFloat(numArray[1])
                };

                coords.push(coordinate);
            }

            //filter coordinates for those shown on the graph
            coords = coords.filter(c => c.x >= 0 && c.x <= svg.getAttribute("width"));
            if (coords[0] !== undefined) {
                let y1 = coords[0].y;
                let y2 = coords[coords.length - 1].y;

                let line = svg.querySelector(".js-line");
                let area = svg.querySelector(".js-fill");

                //change color based on value
                if (y1 < y2) {
                    line.style.stroke = "red";
                    area.style.fill = "red";
                } else if (y1 > y2) {
                    line.style.stroke = "lightgreen";
                    area.style.fill = "lightgreen";
                } else {
                    line.style.stroke = "gold";
                    area.style.fill = "gold";
                };
            } else {
                //prevent looping if zoomed in too far
                svg.querySelector(".js-line").style.stroke = "rgb(211, 211, 212)";
            }

        };

    };
    function getHTML(url, callback) {

      /*  //feature detection
        if (!window.XMLHttpRequest) return;
        //create new request
        let xhr = new XMLHttpRequest();

        //setup callback
        xhr.onload = function () {
            if (callback && typeof (callback) === 'function') {
                callback(this.responseXML);
            }
        }

        //get the HTML
        xhr.open('GET', url);
        xhr.responseType = 'document';
        xhr.send();*/
        fetch(url)
        .then(response => response.json())
        .then(graph => {
            var temp = document.createElement('div');
            temp.innerHTML = graph;
            var htmlObject = temp.firstChild;
            callback(htmlObject);
        });

    };
    function appendGraph(response) {
        /*let graphD = response.querySelector("div");
        graph.innerHTML = '';
        graph.appendChild(graphD);
        let scripts = graph.querySelectorAll('script').forEach((script) => {
            eval(script.text);
        })*/
        let graphD = response;
        graph.innerHTML = '';
        graph.appendChild(graphD);
        let scripts = graph.querySelectorAll('script').forEach((script) => {
            eval(script.text);
        })
        
    }

    //popovers
    $(document).ready(function () {
        $('[data-toggle="popover"]').popover();
    });

    //news carousel
    const carousel = document.querySelector(".carousel-inner")
    //make api call
    let data = document.querySelector("#news-data").innerText;
    data = JSON.parse(data);
    data.forEach(function (article, index) {
        //set active
        let slide = document.createElement('div');
        if (article === data[0]) {
            slide.className = "carousel-item active";
        } else {
            slide.className = "carousel-item";
        }

        //order slides
        let arr = []
        if (data[index + 2] !== undefined) {
            arr.push(article, data[index + 1], data[index + 2]);
        } else if (index === 4) {
            arr.push(article, data[0], data[1]);
        } else {
            arr.push(article, data[index + 1], data[0]);
        }

        //setup each slide
        arr.forEach(news => {
            let imgC = new Image(width = 320, height = 180);
            imgC.src = news.image;
            let span = document.createElement('span');
            span.className = "news-span";

            let title = document.createElement('a');
            title.href = news.url;
            title.innerHTML = news.headline;

            let para = document.createElement('p');
            para.className = "news-p";
            para.innerHTML = news.summary;

            let br = document.createElement('br');

            //add elements
            span.appendChild(imgC);
            span.appendChild(br);
            span.appendChild(title);
            span.appendChild(para);
            slide.appendChild(span);
        });
        carousel.appendChild(slide);

    });

});