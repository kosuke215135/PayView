//csvを読み込んで配列にする関数
function getCsv(filename){
    // CSVファイルを取得
    let csv = new XMLHttpRequest();
        
    // CSVファイルへのパス
    csv.open("GET", filename, false);

    // csvファイル読み込み失敗時のエラー対応
    try {
    csv.send(null);
    } catch (err) {
    console.log(err);
    }

    // 配列を定義
    let csvArray = [];

    // 改行ごとに配列化
    let lines = csv.responseText.split(/\r\n|\n/);

    // 1行ごとに処理
    for (let i = 0; i < lines.length; ++i) {
        let cells = lines[i].split(",");

        //以下のfor文はダブルクオーテーションで囲われているカンマを無視するための処理
        let combined_cells = [];
        let is_push_combined_cells = true;
        let cell_cache = "";
        let first_char = "";
        let last_char = "";
        for (let j = 0; j < cells.length; j++) {
            first_char = cells[j].slice(0,1);
            last_char = cells[j].slice(-1);
            if (first_char == '"') {
                cell_cache += cells[j].slice(1) + ","; 
                is_push_combined_cells=false; 
            }
            else if (last_char == '"') {
                cell_cache += cells[j].slice(0,-1); 
                is_push_combined_cells=true; 
                combined_cells.push(cell_cache); 
                cell_cache = ""
            }
            else if (is_push_combined_cells) {
                combined_cells.push(cells[j]) 
            }
            else {
                cell_cache += cells[j] + ",";
            }
        }
        csvArray.push(combined_cells);
    }
    return csvArray;
}


function loadShopNames(csvArray, contents_url) {
    const shopList = document.getElementsByClassName("slideFlame");

    // 以前の内容をクリアする
    shopList.innerHTML = '';

    for (let i=1; i < csvArray.length; i++){
        const slideBox = document.createElement("div");
        slideBox.classList.add("slideBox");
        const slideLine = document.createElement("div");
        slideLine.classList.add("slideLine");
        const shopLocation = document.createElement("div");
        shopLocation.classList.add("location");
        const genzaiti = document.createElement("span");
        genzaiti.innerHTML = "現在地から〜";
        genzaiti.classList.add("genzaiti");
        const km = document.createElement("span");
        km.innerHTML = "km";
        km.classList.add("km");
        shopLocation.appendChild(genzaiti);
        shopLocation.appendChild(km);
        const storeName = document.createElement("span");
        storeName.innerHTML = csvArray[i][1];
        storeName.classList.add("storeName");
        const payment = document.createElement("div");
        payment_str = csvArray[i][4];
        console.log(payment_str);      
        if (payment_str.length > 100) {
            payment_str = payment_str.slice(0,100) + "...";
        }
        console.log(payment_str);
        payment.innerHTML = payment_str;
        payment.classList.add("payment");

        slideBox.appendChild(slideLine);
        slideBox.appendChild(storeName);
        slideBox.appendChild(shopLocation);
        slideBox.appendChild(payment);
        shopList[0].appendChild(slideBox); //[0]を付ける理由は"DOM"で調べて.

        slideBox.addEventListener('click', () => {
            window.location.href = contents_url + "detail.html" + "?shopNum=" + csvArray[i][0];  // リンク先のURLを設定
        });
    }
}


function main() {
    let csvArray = getCsv("./shop.csv");
    // top.htmlのurlを獲得
    var top_url = location.href;
    var contents_url  = top_url.slice( 0, -8 ); 
    
    window.onload = loadShopNames(csvArray, contents_url);
}

main();

