# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
import re
import traceback
import requests
import json
from odoo.exceptions import UserError
from odoo.modules import get_module_resource

import json
import os

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    @staticmethod
    def get_master_india_access_token():
        url = "https://pro.mastersindia.co/oauth/access_token"

        access_data_file_path = get_module_resource('youngman_customers', 'static/config.json')

        config = open(access_data_file_path, 'r')

        config = config.read()

        access_data = json.loads(config)
        payload = json.dumps({
            "username": access_data["username"],
            "password": access_data["password"],
            "client_id": access_data["client_id"],
            "client_secret": access_data["client_secret"],
            "grant_type": "password"
        })
        headers = {
            'Content-Type': 'application/json',
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()['access_token'], access_data["client_id"]

    @staticmethod
    def check_gstin_chksum(gstin_num):
        gstin_num = gstin_num.upper()
        keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
                'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        values = range(36)
        hash = {k: v for k, v in zip(keys, values)}
        index = 0
        sum = 0
        while index < len(gstin_num) - 1:
            lettr = gstin_num[index]
            tmp = (hash[lettr]) * ((index % 2) + 1)  # Factor =1 fr index odd
            sum += tmp // 36 + tmp % 36
            index = index + 1
        Z = sum % 36
        Z = (36 - Z) % 36
        if ((hash[(gstin_num[-1:])]) == Z):
            return True
        return False

    def get_country(self, country_code):
        country = self.env['res.country'].search([('code', '=', country_code)], limit=1)
        if country:
            return [country.id, country.name]

    @staticmethod
    def validate_gstn_from_master_india(gstin_num):
        try:
            url = "https://commonapi.mastersindia.co/commonapis/searchgstin?gstin=%s" % (gstin_num)
            _logger.info("Master india api url is %s" % (url))
            acesstoken, clientid = Partner.get_master_india_access_token()
            payload = ""
            headers = {
                'client_id': clientid,
                'Content-type': 'application/json',
                'Authorization': 'Bearer %s' % acesstoken
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            message = "Master India API request failed with code: {}, msg: {}, content: {}, url: {}".format(e.response.status_code, e.response.reason, e.response.content, url)
            _logger.error(message)
            raise UserError(message)

    def _validate_gstn_length(self):
        if len(self.gstn) != 15:
            raise Exception('Invalid GSTIN. GSTIN number must be 15 digits. Please check.')

    def _validate_gstn_pattern(self):
        if not (re.match("\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}", self.gstn.upper())):
            raise Exception('Invalid GSTIN format.\r\n.GSTIN must be in the format nnAAAAAnnnnA_Z_ where n=number, A=alphabet, _=either.')

    def _validate_gstn_checksum(self):
        if not (Partner.check_gstin_chksum(self.gstn)):
            raise Exception('Invalid GSTIN. Checksum validation failed. It means one or more characters are probably wrong.')

    @api.onchange('gstn')
    def do_stuff(self):
        try:
            if not self.gstn or self.is_non_gst_customer or not self.is_company:
                return

            self._validate_gstn_length()
            self._validate_gstn_pattern()
            self._validate_gstn_checksum()

            self.gstn = self.gstn.upper()

            gst_data = Partner.validate_gstn_from_master_india(self.gstn)

            if (gst_data['error']):
                raise Exception("Invalid GSTIN. Remote validation failed. It means the GSTN does not exist or masters india api is down.")

            _logger.warning(gst_data)


            if self.gstn[5] == 'C':
                self.name = gst_data["data"]["lgnm"]
            else:
                if len(gst_data["data"]["tradeNam"]) == 0:
                    self.name = gst_data["data"]["lgnm"]
                else:
                    self.name = gst_data["data"]["tradeNam"]

            self.street = gst_data["data"]["pradr"]["addr"]["bno"] + gst_data["data"]["pradr"]["addr"]["bnm"]
            self.street2 = gst_data["data"]["pradr"]["addr"]["st"]
            self.city = gst_data["data"]["pradr"]["addr"]["city"]
            self.zip = str(gst_data["data"]["pradr"]["addr"]["pncd"]) if gst_data["data"]["pradr"]["addr"]["pncd"] is not None else None
            self.country_id = self.get_country("IN")
            company_type = gst_data['data']['ctb']
            type_id = self.env['business.type'].search([('name', '=', company_type)]).id

            if (type_id):
                self.business_type = type_id
            else:
                values = {'name': company_type}
                self.env['business.type'].create(values)
                type_id = self.env['business.type'].search([('name', '=', company_type)]).id
                self.business_type = type_id

        except Exception as e:
            self.name = False
            self.street = False
            self.street2 = False
            self.city = False
            self.zip = False
            self.business_type = False
            self.bill_submission_process = False

            _logger.error(traceback.format_exc())
            return {
                'warning': {'title': 'Warning', 'message':str(e)}
            }
