from flask import Flask, request, jsonify
from pydantic import BaseModel
from pyairtable import Table
import threading
import functions_framework
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))

class YearMakeModel(BaseModel):
    year: str
    make: str
    model: str
    
class Step(BaseModel):
    address: str
    dob: str
    email: str
    fulllegalname: str
    licensenumber: str
    phonenumber: str
    yearmakemodel: list[YearMakeModel]

class FinalOutput(BaseModel):
    steps: list[Step]


@functions_framework.http
def cxReceiveMessage(request):
    try:
        data = request.get_json()
        params = data['sessionInfo']['parameters']
        address = params['address']
        dob = params['dob']
        email = params['email']
        fulllegalname = params['fulllegalname']
        licensenumber = params['licensenumber']
        phonenumber = params['phonenumber']
        yearmakemodel = params['yearmakemodel']        
        threading.Thread(target=structuredOutput, args = (address,dob,email,fulllegalname,licensenumber,phonenumber,yearmakemodel,)).start()
        return jsonify(
            {
                'fulfillment_response': {
                    'messages': [
                        {
                            'text': {
                                'text': ["Great! We have enough information to get started on your quotes. I will pass this information to a member of my team, and they will message you if there are any additional questions. It usually takes about 24-48 hours to receive quotes from the insurance companies we work with. You will receive a message here as soon as we have some good prices. Thank you again for your patience in answering my questions 🙂"],
                                'redactedText': ["Great! We have enough information to get started on your quotes. I will pass this information to a member of my team, and they will message you if there are any additional questions. It usually takes about 24-48 hours to receive quotes from the insurance companies we work with. You will receive a message here as soon as we have some good prices. Thank you again for your patience in answering my questions 🙂"]
                            },
                            'responseType': 'HANDLER_PROMPT',
                            'source': 'VIRTUAL_AGENT'
                        }
                    ]
                }
            }
        )
    
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500  # Return an error response
    
def structuredOutput(address,dob,email,fulllegalname,licensenumber,phonenumber,yearmakemodel) -> None:
    try:
        completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. You will get the user details and details might contain unnecessory content, You need to filter out the actual data from the details and return it in the list. And you will get make,model,year in one parameter you need to return that in a list as well. And give date of birth in this format: yyyy-mm-dd"},
            {"role": "user", "content": f"Here is the user details: Address: {address}, DateOfBirth: {dob}, email: {email}, LegalName: {fulllegalname}, LicenseNumber: {licensenumber}, Phone Number: {phonenumber}, YearMakeModel: {yearmakemodel}"}
        ],
        response_format=FinalOutput,
        )
        result = completion.choices[0].message.parsed
        my_list = []

        for step in result.steps:
            
            my_list.append(step.address)
            my_list.append(step.dob)
            my_list.append(step.email)
            my_list.append(step.fulllegalname)
            my_list.append(step.licensenumber)
            my_list.append(step.phonenumber)

            for res in step.yearmakemodel:
                my_list.append(res.year)
                my_list.append(res.make)
                my_list.append(res.model)
                
        print(my_list)
        airtable(my_list)
    
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500  # Return an error responsess
    
def airtable(my_list) -> None:
    try:
        AIRTABLE_API_KEY = os.getenv('AIRTABLE_ACCESS_TOKEN')
        BASE_ID = os.getenv('AIRTABLE_BASE_ID')
        TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
        
        table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)
        
        # Fetch all records from the table
            # records = table.all()
            # print(records[0:10])
        
        # Add a new record to the table
        print(my_list[1])
        new_record = {
            "address": my_list[0],
            "dateOfBirth": my_list[1],
            "emailAddress": my_list[2],
            "firstName": my_list[3],
            "dlNumber": my_list[4],
            "phoneNumber": my_list[5],
            "vehicle1Year": my_list[6],
            "vehicle1Make": my_list[7],
            "vehicle1Model": my_list[8],
        }
        response = table.create(new_record)
        print("Record created successfully:", response)
        # Update a record by ID
            # record_id = "rec1234567890"
            # updated_record = {
            #     "Field1": "UpdatedValue1"
            # }
            # table.update(record_id, updated_record)

        # Delete a record by ID
            # table.delete(record_id)
        
        
    except Exception as e:
        print(e)   
        return jsonify({'error': str(e)}), 500  # Return an error response 
         