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
    const shopList = document.getElementById("shopList");

    // 以前の内容をクリアする
    shopList.innerHTML = '';

    for (let i=1; i < csvArray.length; i++){
        const shopName = document.createElement("div");
        shopName.innerHTML = csvArray[i][1];
        shopName.classList.add("shop");
        shopList.appendChild(shopName);

        shopName.addEventListener('click', () => {
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

