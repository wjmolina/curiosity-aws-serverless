import boto3
import json
import urllib3


def lambda_handler(event, context):
    table = boto3.resource("dynamodb").Table("esxdynamoclientinfo")
    response = {"message": "success"}
    
    if "httpMethod" not in event:
        event["httpMethod"] = "PATCH"
    
    if event["httpMethod"] == "GET":
        response = table.get_item(Key={"clientip": clientip}).get("Item")
    elif event["httpMethod"] == "POST":
        clientip = event.get("requestContext", {}).get("identity", {}).get("sourceIp")
        tickers = event.get("querStringParameters", {}).get("tickers", [])
        request_time = event.get("requestContext", {}).get("requestTime")
        if not table.get_item(Key={"clientip": clientip}).get("Item"):
            table.put_item(Item={
                "clientip": clientip,
                "requestTime": request_time,
                "hits": 1,
                "tickers": tickers
            })
        elif request_time:
            table.update_item(
                Key={"clientip": clientip},
                UpdateExpression="set requestTime=:requestTime, hits=if_not_exists(hits,:start)+:increment, tickers=:tickers",
                ExpressionAttributeValues={
                    ":requestTime": request_time,
                    ":start": 0,
                    ":increment": 1,
                    ":tickers": tickers
                }
            )
        else:
            response["message"] = "failure"
    elif event["httpMethod"] == "PATCH":
        items = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr("country").not_exists()).get("Items", [])
        pool_manager = urllib3.PoolManager()
        for item in items:
            item_info = json.loads(pool_manager.request("GET", f"http://ip-api.com/json/{item['clientip']}").data.decode("utf8"))
            table.update_item(
                Key={"clientip": item["clientip"]},
                UpdateExpression="set country=:country, countryCode=:countryCode, regionAbbr=:regionAbbr, regionName=:regionName, city=:city, zip=:zip, tz=:tz, isp=:isp, org=:org, ispas=:ispas",
                ExpressionAttributeValues={
                    ":country": item_info["country"],
                    ":countryCode": item_info["countryCode"],
                    ":regionAbbr": item_info["region"],
                    ":regionName": item_info["regionName"],
                    ":city": item_info["city"],
                    ":zip": item_info["zip"],
                    ":tz": item_info["timezone"],
                    ":isp": item_info["isp"],
                    ":org": item_info["org"],
                    ":ispas": item_info["as"],
                }
            )

    return {
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(response)
    }
