from flask import Flask, jsonify, request, abort
from pymongo import MongoClient
from geopy.geocoders import Nominatim
import RegionFinder

app=Flask(__name__)

def getRegionFromAddress(address):
    geolocation=Nominatim(user_agent="example")
    location=geolocation.geocode(address)
    if location:
        locationCoordinates={'lat':location.latitude,'lng':location.longitude}
        print(locationCoordinates)
        # print(locationCoordinates)
        # print(RegionFinder.findRegion(locationCoordinates))
        return RegionFinder.findRegion(locationCoordinates)

@app.route('/rental/getCompetitorRates', methods=['GET'])
def getCompetitorRates():
    address=request.args.get("address")
    unitType=request.args.get("unitType")
    if address is None:
        abort(400, description='Mandatory query parameter: address not provided')
    elif unitType is None:
        abort(400, description='Mandatory query parameter: unitType not provided')
    mongoUri="mongodb://localhost:27017"
    mongoDatabase="RentalProject"
    mongoCollectionName="RentalData"
    mongoClient=MongoClient(mongoUri)
    mongoDb=mongoClient[mongoDatabase]
    mongoCollection=mongoDb[mongoCollectionName]
    region=getRegionFromAddress(address)
    builders=mongoCollection.distinct("PROPERTY_OWNER")
    builderApiResponse=[]
    for builder in builders:
        # print(builder)
        result=mongoCollection.find({'$and':[{'PROPERTY_OWNER':builder},{'SUITE_TYPE':unitType},{'DISTRICT_REGION':region}]})
        count=0
        rent=[]
        for document in result:
            sqft=document.get('RETAIL_SQUARE_FOOTAGE',0)
            pricePerSqft=document.get('PRICE_PER_SQ_FT',0)
            if sqft>0 and pricePerSqft>0:
                rent.append(round(pricePerSqft*sqft))
                # print("Rent:",rent[-1])
                count+=1
        if count==1:
            competitorRate={'Builder':builder,'Rent':rent[-1]}
        elif count>1:
            competitorRate={'Builder':builder,'Rent':round(sum(rent)/count,2)}
        if count>0:
            builderApiResponse.append(competitorRate)
    print(builderApiResponse)
    
    mongoClient.close()
    return builderApiResponse

@app.errorhandler(400)
def handleBadRequest(error):
    response=jsonify({'error':error.description})
    response.status_code=error.code
    return response

if __name__=='__main__':
    app.run(debug=True)