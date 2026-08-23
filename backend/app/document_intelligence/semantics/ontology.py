import re
from enum import Enum
from typing import List, Dict, Set, Optional
from pydantic import BaseModel

class ValueType(str, Enum):
    PERSON_NAME = "PERSON_NAME"
    PHONE_NUMBER = "PHONE_NUMBER"
    EMAIL = "EMAIL"
    DATE = "DATE"
    TIME = "TIME"
    CURRENCY = "CURRENCY"
    PERCENTAGE = "PERCENTAGE"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    IDENTIFIER = "IDENTIFIER"
    GSTIN = "GSTIN"
    PAN = "PAN"
    CIN = "CIN"
    IFSC = "IFSC"
    SWIFT = "SWIFT"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    ADDRESS = "ADDRESS"
    POSTAL_CODE = "POSTAL_CODE"
    FLIGHT_NUMBER = "FLIGHT_NUMBER"
    TICKET_NUMBER = "TICKET_NUMBER"
    URL = "URL"
    TEXT = "TEXT"
    UNKNOWN = "UNKNOWN"

class OntologyEntry(BaseModel):
    canonical_name: str
    display_label: str
    compatible_value_types: List[ValueType]
    aliases: List[str]
    description: str = ""

# Canonical Semantic Ontology Registry
CANONICAL_ONTOLOGY: Dict[str, OntologyEntry] = {
    "person_name": OntologyEntry(
        canonical_name="person_name",
        display_label="Person Name",
        compatible_value_types=[ValueType.PERSON_NAME, ValueType.TEXT],
        aliases=["name", "full name", "person name", "contact person", "applicant", "customer name", "client name"],
        description="Full name of an individual person"
    ),
    "contact_number": OntologyEntry(
        canonical_name="contact_number",
        display_label="Contact Number",
        compatible_value_types=[ValueType.PHONE_NUMBER, ValueType.INTEGER, ValueType.IDENTIFIER],
        aliases=["phone", "ph", "ph.", "mobile", "contact", "telephone", "tel", "mobile no", "contact no", "phone no", "mobile number"],
        description="Telephone or mobile contact number"
    ),
    "email_address": OntologyEntry(
        canonical_name="email_address",
        display_label="Email Address",
        compatible_value_types=[ValueType.EMAIL, ValueType.TEXT],
        aliases=["e-mail", "email", "mail", "email id"],
        description="Electronic mail contact address"
    ),
    "website_url": OntologyEntry(
        canonical_name="website_url",
        display_label="Website URL",
        compatible_value_types=[ValueType.URL, ValueType.TEXT],
        aliases=["website", "web", "url", "site", "web address"],
        description="Web portal URL"
    ),
    "vendor_name": OntologyEntry(
        canonical_name="vendor_name",
        display_label="Vendor Name",
        compatible_value_types=[ValueType.TEXT, ValueType.PERSON_NAME],
        aliases=["vendor", "merchant", "biller", "company", "seller", "issuer", "provider"],
        description="Name of issuing vendor or merchant"
    ),
    "customer_name": OntologyEntry(
        canonical_name="customer_name",
        display_label="Customer Name",
        compatible_value_types=[ValueType.PERSON_NAME, ValueType.TEXT],
        aliases=["customer", "client", "bill to", "billed to", "booker", "buyer"],
        description="Name of recipient customer or entity"
    ),
    "invoice_number": OntologyEntry(
        canonical_name="invoice_number",
        display_label="Invoice Number",
        compatible_value_types=[ValueType.IDENTIFIER, ValueType.INTEGER, ValueType.TEXT],
        aliases=["invoice no.", "invoice no", "invoice number", "inv. no.", "bill no", "tax invoice no.", "lead no.", "lead no", "bill number", "receipt no"],
        description="Unique bill/invoice identification string"
    ),
    "invoice_date": OntologyEntry(
        canonical_name="invoice_date",
        display_label="Invoice Date",
        compatible_value_types=[ValueType.DATE, ValueType.TEXT],
        aliases=["date", "invoice date", "bill date", "dated", "issue date", "posting date"],
        description="Official document issuance date"
    ),
    "travel_date": OntologyEntry(
        canonical_name="travel_date",
        display_label="Travel Date",
        compatible_value_types=[ValueType.DATE, ValueType.TEXT],
        aliases=["travel dt.", "travel date", "departure date", "flight date", "journey date", "travel dt"],
        description="Scheduled travel or booking date"
    ),
    "gstin": OntologyEntry(
        canonical_name="gstin",
        display_label="GST Identification Number",
        compatible_value_types=[ValueType.GSTIN, ValueType.IDENTIFIER],
        aliases=["gstin", "gst no", "gst", "gstin/uin", "vat no", "gst number"],
        description="15-character Goods and Services Tax Identification Number"
    ),
    "pan": OntologyEntry(
        canonical_name="pan",
        display_label="Permanent Account Number",
        compatible_value_types=[ValueType.PAN, ValueType.IDENTIFIER],
        aliases=["pan", "pan no", "pan number"],
        description="Permanent Account Number (PAN)"
    ),
    "cin": OntologyEntry(
        canonical_name="cin",
        display_label="Corporate Identification Number",
        compatible_value_types=[ValueType.CIN, ValueType.IDENTIFIER],
        aliases=["cin", "cin no", "cin number"],
        description="21-digit Corporate Identification Number"
    ),
    "udyam_number": OntologyEntry(
        canonical_name="udyam_number",
        display_label="Udyam Registration Number",
        compatible_value_types=[ValueType.IDENTIFIER, ValueType.TEXT],
        aliases=["udyam no.", "udyam no", "udyam number", "udyam reg no"],
        description="MSME Udyam registration code"
    ),
    "taxable_amount": OntologyEntry(
        canonical_name="taxable_amount",
        display_label="Taxable Amount",
        compatible_value_types=[ValueType.CURRENCY, ValueType.DECIMAL, ValueType.INTEGER],
        aliases=["taxable value", "taxable amount", "subtotal", "sub-total", "taxable val"],
        description="Subtotal before taxes"
    ),
    "total_amount": OntologyEntry(
        canonical_name="total_amount",
        display_label="Total Amount",
        compatible_value_types=[ValueType.CURRENCY, ValueType.DECIMAL, ValueType.INTEGER],
        aliases=["total", "net amount", "total amount", "amount due", "grand total", "total pay"],
        description="Final gross amount"
    ),
    "cgst_rate": OntologyEntry(
        canonical_name="cgst_rate",
        display_label="CGST Rate",
        compatible_value_types=[ValueType.PERCENTAGE, ValueType.DECIMAL],
        aliases=["cgst %", "cgst rate", "cgst percent"],
        description="Central GST percentage rate"
    ),
    "cgst_amount": OntologyEntry(
        canonical_name="cgst_amount",
        display_label="CGST Amount",
        compatible_value_types=[ValueType.CURRENCY, ValueType.DECIMAL],
        aliases=["cgst amount", "cgst", "cgst amt"],
        description="Central GST monetary total"
    ),
    "sgst_rate": OntologyEntry(
        canonical_name="sgst_rate",
        display_label="SGST Rate",
        compatible_value_types=[ValueType.PERCENTAGE, ValueType.DECIMAL],
        aliases=["sgst %", "sgst rate", "sgst percent"],
        description="State GST percentage rate"
    ),
    "sgst_amount": OntologyEntry(
        canonical_name="sgst_amount",
        display_label="SGST Amount",
        compatible_value_types=[ValueType.CURRENCY, ValueType.DECIMAL],
        aliases=["sgst amount", "sgst", "sgst amt"],
        description="State GST monetary total"
    ),
    "igst_rate": OntologyEntry(
        canonical_name="igst_rate",
        display_label="IGST Rate",
        compatible_value_types=[ValueType.PERCENTAGE, ValueType.DECIMAL],
        aliases=["igst %", "igst rate", "igst percent"],
        description="Integrated GST percentage rate"
    ),
    "igst_amount": OntologyEntry(
        canonical_name="igst_amount",
        display_label="IGST Amount",
        compatible_value_types=[ValueType.CURRENCY, ValueType.DECIMAL],
        aliases=["igst amount", "igst", "igst amt"],
        description="Integrated GST monetary total"
    ),
    "vat_rate": OntologyEntry(
        canonical_name="vat_rate",
        display_label="VAT Rate",
        compatible_value_types=[ValueType.PERCENTAGE, ValueType.DECIMAL],
        aliases=["vat %", "vat rate"],
        description="Value Added Tax percentage rate"
    ),
    "vat_amount": OntologyEntry(
        canonical_name="vat_amount",
        display_label="VAT Amount",
        compatible_value_types=[ValueType.CURRENCY, ValueType.DECIMAL],
        aliases=["vat amount", "vat"],
        description="Value Added Tax monetary total"
    ),
    "passenger_name": OntologyEntry(
        canonical_name="passenger_name",
        display_label="Passenger Name",
        compatible_value_types=[ValueType.PERSON_NAME, ValueType.TEXT],
        aliases=["passenger", "passenger name", "guest", "guest name", "pax", "pax name"],
        description="Traveler or guest name"
    ),
    "ticket_number": OntologyEntry(
        canonical_name="ticket_number",
        display_label="Ticket Number",
        compatible_value_types=[ValueType.IDENTIFIER, ValueType.INTEGER, ValueType.TEXT],
        aliases=["ticket no.", "ticket no", "ticket number", "eticket", "e-ticket"],
        description="Transport ticket code"
    ),
    "flight_number": OntologyEntry(
        canonical_name="flight_number",
        display_label="Flight Number",
        compatible_value_types=[ValueType.IDENTIFIER, ValueType.TEXT],
        aliases=["flight no", "flight", "flight number", "flight no."],
        description="Airline flight code"
    ),
    "departure_location": OntologyEntry(
        canonical_name="departure_location",
        display_label="Departure Location",
        compatible_value_types=[ValueType.TEXT],
        aliases=["from", "departure", "origin", "place of supply", "sector"],
        description="Origin or departure place"
    ),
    "arrival_location": OntologyEntry(
        canonical_name="arrival_location",
        display_label="Arrival Location",
        compatible_value_types=[ValueType.TEXT],
        aliases=["to", "arrival", "destination"],
        description="Destination place"
    ),
    "bank_name": OntologyEntry(
        canonical_name="bank_name",
        display_label="Bank Name",
        compatible_value_types=[ValueType.TEXT],
        aliases=["bank", "bank name"],
        description="Name of banking institution"
    ),
    "bank_account_number": OntologyEntry(
        canonical_name="bank_account_number",
        display_label="Bank Account Number",
        compatible_value_types=[ValueType.BANK_ACCOUNT, ValueType.IDENTIFIER, ValueType.INTEGER],
        aliases=["account number", "acc no", "a/c no", "account no.", "account no", "ac no"],
        description="Bank account number string"
    ),
    "bank_account_name": OntologyEntry(
        canonical_name="bank_account_name",
        display_label="Account Holder Name",
        compatible_value_types=[ValueType.PERSON_NAME, ValueType.TEXT],
        aliases=["account name", "account holder", "a/c name", "account title"],
        description="Beneficiary account title"
    ),
    "ifsc_code": OntologyEntry(
        canonical_name="ifsc_code",
        display_label="IFSC Code",
        compatible_value_types=[ValueType.IFSC, ValueType.IDENTIFIER],
        aliases=["ifsc code", "ifsc", "ifsc no"],
        description="Indian Financial System Code"
    ),
    "swift_code": OntologyEntry(
        canonical_name="swift_code",
        display_label="SWIFT Code",
        compatible_value_types=[ValueType.SWIFT, ValueType.IDENTIFIER],
        aliases=["swift code", "swift", "bic", "swift/bic"],
        description="Society for Worldwide Interbank Financial Telecommunication code"
    ),
    "address": OntologyEntry(
        canonical_name="address",
        display_label="Address",
        compatible_value_types=[ValueType.ADDRESS, ValueType.TEXT],
        aliases=["address", "delivery address", "billing address", "street address", "location"],
        description="Physical location or mailing address"
    ),
    "postal_code": OntologyEntry(
        canonical_name="postal_code",
        display_label="Postal Code",
        compatible_value_types=[ValueType.POSTAL_CODE, ValueType.INTEGER],
        aliases=["pincode", "zip code", "postal code", "pin code", "zip"],
        description="Postal ZIP or PIN code"
    ),
    "unknown_field": OntologyEntry(
        canonical_name="unknown_field",
        display_label="Unknown Field",
        compatible_value_types=[ValueType.UNKNOWN, ValueType.TEXT],
        aliases=[],
        description="Unclassified or generic custom field"
    )
}

def detect_value_type(text: str) -> ValueType:
    raw = text.strip()
    if not raw:
        return ValueType.UNKNOWN

    # GSTIN (15 chars: e.g., 07AAACS0229G1ZR)
    if re.search(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b', raw):
        return ValueType.GSTIN

    # PAN (10 chars: e.g., ABCDE1234F)
    if re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', raw):
        return ValueType.PAN

    # IFSC (11 chars: e.g., SBIN0001234)
    if re.search(r'\b[A-Z]{4}0[A-Z0-9]{6}\b', raw):
        return ValueType.IFSC

    # Email
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', raw):
        return ValueType.EMAIL

    # Phone Number (10+ digits, optional + prefix)
    if re.search(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', raw) and sum(c.isdigit() for c in raw) >= 10:
        return ValueType.PHONE_NUMBER

    # Currency ($600.00, ₹600.00, INR 500, USD 20)
    if re.search(r'[\$₹€£]|inr|usd|eur', raw, re.I) or re.search(r'^\d+[\.,]\d{2}$', raw):
        return ValueType.CURRENCY

    # Percentage (18%, 5.5%)
    if "%" in raw or re.search(r'\b\d+(\.\d+)?\s*percent\b', raw, re.I):
        return ValueType.PERCENTAGE

    # Date (20/08/2026, 2026-08-20, 20 Aug 2026)
    if re.search(r'\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b', raw) or re.search(r'\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', raw, re.I):
        return ValueType.DATE

    # URL
    if re.search(r'https?://|www\.', raw, re.I):
        return ValueType.URL

    # Person Name (2-3 title cased words without digits or symbols)
    words = raw.split()
    if 2 <= len(words) <= 3 and all(w[0].isupper() and w.isalpha() for w in words):
        return ValueType.PERSON_NAME

    # Identifier (INV-1024, PNR-991, 015405004824)
    if re.search(r'^[A-Z0-9]{3,}[-/#]?[A-Z0-9]{2,}$', raw) and any(c.isdigit() for c in raw):
        return ValueType.IDENTIFIER

    # Pure Integer
    if re.match(r'^\d+$', raw):
        return ValueType.INTEGER

    # Pure Decimal
    if re.match(r'^\d+\.\d+$', raw):
        return ValueType.DECIMAL

    return ValueType.TEXT
