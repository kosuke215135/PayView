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


//urlからクエリを得る関数
function getUrlQueries() {
    var queryStr = window.location.search.slice(1);  // 文頭?を除外
        queries = {};
        
    // クエリがない場合は空のオブジェクトを返す
    if (!queryStr) {
      return queries;
    }
    
    // クエリ文字列を & で分割して処理
    queryStr.split('&').forEach(function(queryStr) {
      // = で分割してkey,valueをオブジェクトに格納
      var queryArr = queryStr.split('=');
      queries[queryArr[0]] = queryArr[1];
    });
    return queries;
}


function main() {
    
    let csvArray = getCsv("./shop.csv");

    let shopNum = getUrlQueries()["shopNum"];

    let shop_detail = csvArray[shopNum];
    let shopName_str = shop_detail[1];
    let shopSettlement_str = shop_detail[4];

    const shopDetail = document.getElementById("shopDetail");

    // 以前の画像をクリアする
    shopDetail.innerHTML = '';

    const shopName = document.createElement("h2");
    shopName.innerHTML = shopName_str;
    shopName.classList.add("shopName");
    shopDetail.appendChild(shopName);

    const paymentService = document.createElement("div");
    paymentService.innerHTML = shopSettlement_str;
    shopDetail.appendChild(paymentService);
}

main();
