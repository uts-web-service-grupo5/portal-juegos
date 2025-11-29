from xml.etree import ElementTree as ET

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.catalog_database import SessionLocal as CatSessionLocal
from app.subscription_database import SessionLocal as SubSessionLocal
from app.user_database import SessionLocal as UserSessionLocal
from app.domain.catalog_model import CatalogAccessRequest
from app.service.catalog_service import CatalogService
from app.service.user_service import UserService
from app.config.settings import settings

router = APIRouter(prefix="/soap/v1", tags=["SOAP"])

WSDL_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="http://portal-juegos.com/soap"
             name="PortalJuegosSOAP"
             targetNamespace="http://portal-juegos.com/soap">
  <types/>
  <message name="CatalogAccessRequest">
    <part name="id_cliente" type="xsd:int"/>
  </message>
  <message name="CatalogAccessResponse">
    <part name="resultado" type="xsd:string"/>
  </message>
  <portType name="PortalJuegosPortType">
    <operation name="CatalogAccess">
      <input message="tns:CatalogAccessRequest"/>
      <output message="tns:CatalogAccessResponse"/>
    </operation>
  </portType>
  <binding name="PortalJuegosBinding" type="tns:PortalJuegosPortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <operation name="CatalogAccess">
      <soap:operation soapAction="CatalogAccess"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
  </binding>
  <service name="PortalJuegosService">
    <port name="PortalJuegosPort" binding="tns:PortalJuegosBinding">
      <soap:address location="{settings.soap_url}"/>
    </port>
  </service>
</definitions>
"""


def _soap_fault(code: str, message: str, status_code: int = 500) -> Response:
    envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
    body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
    fault = ET.SubElement(body, "Fault")
    ET.SubElement(fault, "faultcode").text = code
    ET.SubElement(fault, "faultstring").text = message
    xml_bytes = ET.tostring(envelope, encoding="utf-8", xml_declaration=True)
    return Response(content=xml_bytes, media_type="text/xml", status_code=status_code)


@router.get("/wsdl")
def wsdl():
    return Response(content=WSDL_TEMPLATE, media_type="text/xml")


@router.post("/")
def soap_entrypoint(request_body: str):
    try:
        root = ET.fromstring(request_body)
    except ET.ParseError:
        return _soap_fault("Client", "XML no válido", status_code=400)

    body = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Body")
    if body is None or len(body) == 0:
        return _soap_fault("Client", "Body vacío", status_code=400)

    operation = body[0]
    op_name = operation.tag.split("}")[-1]

    if op_name.lower() in {"catalogaccess", "catalogaccessrequest"}:
        id_text = operation.findtext("id_cliente") or operation.findtext("idCliente")
        if not id_text or not id_text.isdigit():
            return _soap_fault("Client", "id_cliente faltante o inválido", status_code=400)
        id_cliente = int(id_text)
        # Servicios y sesiones
        cat_db = CatSessionLocal()
        user_db = UserSessionLocal()
        sub_db = SubSessionLocal()
        try:
            user_service = UserService(user_db, sub_db)
            user_service.decode_token = lambda token: None  # No se usa token aquí; solo reusar lógica de acceso
            catalog_service = CatalogService(cat_db, user_db, sub_db)
            data = catalog_service.acceso_catalogo(CatalogAccessRequest(id_cliente=id_cliente))
        except HTTPException as exc:
            return _soap_fault("Server" if exc.status_code >= 500 else "Client", exc.detail, status_code=exc.status_code)
        finally:
            cat_db.close()
            user_db.close()
            sub_db.close()

        envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
        body_resp = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
        resp = ET.SubElement(body_resp, "CatalogAccessResponse")
        cliente_node = ET.SubElement(resp, "cliente")
        ET.SubElement(cliente_node, "id_cliente").text = str(data.data["cliente"]["id_cliente"])
        ET.SubElement(cliente_node, "edad").text = str(data.data["cliente"]["edad"])
        ET.SubElement(cliente_node, "plan").text = data.data["cliente"]["plan"]

        juegos_node = ET.SubElement(resp, "juegos_disponibles")
        for juego in data.data["juegos_disponibles"]:
            jnode = ET.SubElement(juegos_node, "juego")
            ET.SubElement(jnode, "id_videojuego").text = str(juego["id_videojuego"])
            ET.SubElement(jnode, "nombre_juego").text = juego["nombre_juego"]
            ET.SubElement(jnode, "restriccion_edad").text = str(juego["restriccion_edad"])
            ET.SubElement(jnode, "acceso_plan").text = juego["acceso_plan"]

        xml_bytes = ET.tostring(envelope, encoding="utf-8", xml_declaration=True)
        return Response(content=xml_bytes, media_type="text/xml")

    return _soap_fault("Client", f"Operación SOAP no soportada: {op_name}", status_code=400)
