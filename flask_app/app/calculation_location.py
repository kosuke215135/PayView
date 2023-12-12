import math

# 現在地からお店まで〜kmか出力する関数
def location_distance(user_latitude, user_longitude, store_latitude, store_longitude):
    # 地球の半径（キロメートル）
    R = 6371.0

    # 緯度経度をラジアンに変換
    lat1 = math.radians(user_latitude)
    lon1 = math.radians(user_longitude)
    lat2 = math.radians(store_latitude)
    lon2 = math.radians(store_longitude)

    # 緯度と経度の差
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # ハーヴァーサイン公式
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # 距離
    distance = R * c

    return distance

def get_distanced_lat_lng(lat, lng, distance):
    R = math.pi / 180  # 円周率をラジアンに変換
    earth_radius = 6371  # 地球の半径（キロメートル）
    kilometer_per_degree = R * earth_radius  # 1度あたりのキロメートル
    degree_per_kilometer = 1 / kilometer_per_degree  # 1キロメートルあたりの度
    diff = distance * degree_per_kilometer  # 指定された距離を角度に変換
    return {'n': lat + diff, 'e': lng + diff, 's': lat - diff, 'w': lng - diff}


# リストを受け取り、各要素の3番目([2])の距離をkmもしくはmに変換する
def conversion_km_or_m(shop_data_list):
    distance = shop_data_list[2]
    if distance >= 1:
        distance = f"{round(distance, 1)} km"
    else:
        distance = f"{int(round(distance, 3) * 1000)} m"
    shop_data_list[2] = distance
    return shop_data_list
    