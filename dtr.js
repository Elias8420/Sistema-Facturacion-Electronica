import {Sales} from '../models/Sales.js';
import { SaleDetails } from '../models/SaleDetails.js';
import { TiketConfiguration } from '../models/TiketConfiguration.js';
import { Buttons } from '../models/Buttons.js';
import { Modifiers} from '../models/Modifiers.js';
import {PaymentMethods} from '../models/PaymentMethods.js'
import { PaymentMethodDetails } from '../models/PaymentMethodDetails.js';
import { NumeroALetras } from '../global/mask.js';
import { Customers } from '../models/Customers.js';
import { Municipios } from '../models/Municipios.js';
import { Departamentos } from '../models/Departamentos.js';
import axios from 'axios';
import crypto from 'crypto';
import moment from 'moment';
import { Correlatives } from '../models/Correlatives.js';
import { User } from '../models/User.js';
import { Employee } from '../models/Employee.js';
import { ApiCredential } from '../models/ApiCredential.js';


export const dteFac = async (id) => {
    try {
        const sales = await Sales.findOne({
            where:{
                saleID:id,
            },
            include:[
                {model:SaleDetails, 
                    include:[
                    {model:Buttons},
                    {model:Modifiers},
                    ]
                },
                {model:PaymentMethodDetails,
                    include:[{model:PaymentMethods}]
                },{model:Customers,
                    include:[{model:Municipios,
                        include:{model:Departamentos}
                    }]
                }
            ]
        });
        
        const emisor = await dteEmisor();
        let receptor = null;
        if(sales.customerDoc != null && sales.customerDoc != ''){
            receptor = {
                "tipoDocumento": sales.customer.documentType,
                "numDocumento": sales.customer.documentType == '13'? sales.customer.customerDoc: sales.customer.customerDoc.trim().replace(/-/g, ''),
                "nrc": sales.customer.nrc ? sales?.customer?.nrc?.trim().replace(/-/g, '') : null,
                "nombre": sales.customer.customerName,
                "codActividad": sales.customer.activityCode,
                "descActividad": sales.customer.activity,
                "direccion":sales.customer?.municipio?.departamento?.codeMH ?{
                    "departamento": sales.customer?.municipio?.departamento?.codeMH ? sales.customer?.municipio?.departamento?.codeMH : null,
                    "municipio": sales?.customer?.municipio?.codeMH ? sales?.customer?.municipio.codeMH : null ,
                    "complemento": sales.customer.address == null ? 'El Salvador C.A' : sales.customer.address
                }:null,
                "telefono": sales.customer.tel,
                "correo": sales.customer.email
            };
        } else {
            receptor = {
                "tipoDocumento":null,
                "numDocumento":null,
                "nrc":null,
                "nombre": sales.client || 'CLIENTES VARIOS',
                "codActividad":null,
                "descActividad":null,
                "direccion":null,
                "telefono":null,
                "correo":null
            }
        }

        const facBody = sales.saleDetails.map((saleDetail) => {
            return {
                "numItem": saleDetail.line,
                "tipoItem": 1,
                "cantidad": parseFloat((saleDetail.cant).toFixed(2)),
                "codigo": saleDetail.itemCode,
                "codTributo":null,
                "uniMedida": 59,
                "descripcion": [saleDetail.button && saleDetail.button.buttonName, saleDetail.modifier && saleDetail.modifier.modifierName].find(name => name != null),
                "precioUni": parseFloat((saleDetail.price).toFixed(4)),
                "montoDescu": parseFloat((saleDetail.discountLine).toFixed(4)),
                "ventaNoSuj": 0.00,
                "ventaExenta": sales.exempt ? parseFloat((saleDetail.totalWithDiscount).toFixed(4)) : 0.00,
                "ventaGravada": !sales.exempt ? parseFloat((saleDetail.totalWithDiscount).toFixed(4)) : 0.00,
                "ivaItem": !sales.exempt ? parseFloat((parseFloat(saleDetail.totalWithDiscount)-parseFloat(saleDetail.totalWithDiscount/1.13)).toFixed(4)) : 0.00,
                "tributos":null,
                "psv": 0.00,
                "noGravado": 0.00,
                "numeroDocumento":null
            }
        }).sort((a, b) => a.numItem - b.numItem)

        const apiCredential = await ApiCredential.findOne({ attributes: ['sandBox'], where: { apiCode: 'MH_FE' } });

        return {
            "identificacion": {
                "version": 1,
                "ambiente": apiCredential.sandBox == 1 ? '00' : '01',
                "tipoDte": "01",
                // retorna despues de enviar el json al ministerio
                "numeroControl": sales.dteControlNumber,
                // hay que crear el codigo de generacion
                "codigoGeneracion": sales.dteGenerationCode,
                // modelo previo
                "tipoModelo": 1,
                // 1:normal - 2:contingencia
                "tipoOperacion": 1,
                "tipoContingencia": null,
                "motivoContin": null,
                "fecEmi": sales.dateCreated,
                "horEmi": sales.hourCreated,
                "tipoMoneda": "USD"
            },
            "documentoRelacionado":null,
            "emisor": emisor,
            "receptor": receptor,
            "otrosDocumentos":null,
            "ventaTercero": null,
            // se creara un bucle para su creacion
            "cuerpoDocumento": facBody,
            "resumen":{
                "totalNoSuj": 0,
                "totalExenta": sales.exempt ? parseFloat((sales.totalWithTax).toFixed(2)) : 0.00,
                "totalGravada": !sales.exempt ? parseFloat((sales.totalWithTax).toFixed(2)) : 0.00,
                "subTotalVentas": parseFloat((sales.totalWithTax).toFixed(2)),
                "descuNoSuj": 0.00,
                "descuExenta": sales.exempt ? parseFloat((sales.totalDiscount).toFixed(2)) : 0.00,
                "descuGravada": !sales.exempt ? parseFloat((sales.totalDiscount).toFixed(2)) : 0.00,
                "porcentajeDescuento": 0,
                "totalDescu":parseFloat((sales.totalDiscount).toFixed(2)),
                "tributos":null,
                "subTotal": parseFloat((sales.totalWithDiscount + (sales.ivaRetenido || 0)).toFixed(2)),
                "ivaRete1": parseFloat((sales.ivaRetenido || 0).toFixed(2)),
                "reteRenta":0.00,
                "montoTotalOperacion": parseFloat((sales.totalWithDiscount + (sales.ivaRetenido || 0)).toFixed(2)),
                "totalNoGravado": 0.00,
                "totalPagar": parseFloat((sales.totalWithDiscount).toFixed(2)),
                "totalLetras": NumeroALetras(parseFloat((sales.totalWithDiscount).toFixed(2))),
                "totalIva": !sales.exempt ? parseFloat((sales.totalTax).toFixed(2)) : 0.00,
                "saldoFavor": 0.00,
                "condicionOperacion": 1,
                "pagos": [
                    {
                        "montoPago":parseFloat((sales.totalWithDiscount).toFixed(2)),
                        "codigo": sales.paymentMethodDetail.paymentMethod.codeMH,
                        "referencia": `${sales.paymentMethodDetail.paymentMethod.paymentMethodName}`,
                        "plazo": null,
                        "periodo": null
                    }
                ],
                "numPagoElectronico": null
                
            },
            "extension": {   
                "nombEntrega": null,    
                "docuEntrega": null,    
                "nombRecibe": null,    
                "docuRecibe": null,    
                "observaciones": null,    
                "placaVehiculo": null   
            },
            "apendice": null
        };
        
    } catch (error) {
        console.log(error);
        return error;
    }
    
}

//function to create dte for CCF
export const dteCcf = async (id) => {
    try {
        const sale = await Sales.findOne({
            where:{
                saleID:id,
            },
            include:[
                {model:SaleDetails, 
                    include:[
                    {model:Buttons},
                    {model:Modifiers},
                    ]
                },
                {model:PaymentMethodDetails,
                    include:[{model:PaymentMethods}]
                },{model:Customers,
                    include:[{
                        model: Municipios,
                        include: { model:Departamentos }
                    }]
                }
            ]
        });
        
        const emisor = await dteEmisor("03");

        let receptor = null;
        if(sale.customerDoc != null && sale.customerDoc != ''){
            receptor = {
                "nit": sale.customer.customerDoc.trim().replace(/-/g, ''),
                "nrc": sale.customer.nrc.trim().replace(/-/g, ''),
                "nombre": sale.customer.customerName,
                "codActividad": sale.customer.activityCode,
                "descActividad": sale.customer.activity,
                "nombreComercial": sale.customer.comercialName,
                "direccion": sale?.customer?.municipioID ?{
                    "departamento": sale.customer?.municipio?.departamento.codeMH,
                    "municipio": sale?.customer?.municipio.codeMH,
                    "complemento": sale.customer.address
                }:null,
                "telefono": sale.customer.tel,
                "correo": sale.customer.email
            };
        }

        const dteBody = sale.saleDetails.map((saleDetail) => ({
            "numItem": saleDetail.line,
            "tipoItem": 1,
            "numeroDocumento": null,
            "codigo": saleDetail.itemCode,
            "codTributo": null,
            "descripcion": [saleDetail.button && saleDetail.button.buttonName, saleDetail.modifier && saleDetail.modifier.modifierName].find(name => name != null),
            "cantidad": parseFloat((saleDetail.cant).toFixed(2)),
            "uniMedida": 59,
            "precioUni": parseFloat((saleDetail.price/1.13).toFixed(4)),
            "montoDescu": parseFloat((saleDetail.discountLine).toFixed(4)),
            "ventaNoSuj": 0.00,
            "ventaExenta": 0.00,
            "ventaGravada": parseFloat((saleDetail.totalWithDiscount/1.13).toFixed(4)),
            "tributos": ["20"],
            "psv": 0.00,
            "noGravado": 0.00,
        }));

        const apiCredential = await ApiCredential.findOne({ attributes: ['sandBox'], where: { apiCode: 'MH_FE' } });
        return {
            "identificacion": {
                "version": 3,
                "ambiente": apiCredential.sandBox == 1 ? '00' : '01',
                "tipoDte": "03",
                "numeroControl": sale.dteControlNumber,
                "codigoGeneracion": sale.dteGenerationCode,
                // 1:previo - 2:diferido
                "tipoModelo": 1,
                // 1:normal - 2:contingencia
                "tipoOperacion": 1,
                "tipoContingencia": null,
                "motivoContin": null,
                "fecEmi": sale.dateCreated,
                "horEmi": sale.hourCreated,
                "tipoMoneda": "USD"
            },
            "documentoRelacionado": null,
            "emisor": emisor,
            "receptor": receptor,
            "otrosDocumentos": null,
            "ventaTercero": null,
            "cuerpoDocumento": dteBody,
            "resumen": {
                "totalNoSuj": 0,
                "totalExenta": 0,
                "totalGravada": parseFloat((sale.totalWithTax/1.13).toFixed(2)),
                "totalNoGravado": 0,
                "subTotalVentas": parseFloat((sale.totalWithTax/1.13).toFixed(2)),
                "descuNoSuj": 0.00,
                "descuExenta": 0.00,
                "descuGravada": parseFloat((sale.totalDiscount/1.13).toFixed(2)),
                "porcentajeDescuento": 0,
                "totalDescu": parseFloat((sale.totalDiscount/1.13).toFixed(2)),
                "tributos": [{
                    "codigo": "20",
                    "descripcion": "Impuesto al Valor Agregado 13%",
                    "valor": parseFloat((sale.totalTax).toFixed(2)),
                
                }],
                "subTotal": parseFloat(((sale.totalWithDiscount + (sale.ivaRetenido || 0))/1.13).toFixed(2)),
                "ivaPerci1": 0.00,
                "ivaRete1": parseFloat((sale.ivaRetenido || 0).toFixed(2)),
                "reteRenta": 0.00,
                "montoTotalOperacion": parseFloat((sale.totalWithDiscount + (sale.ivaRetenido || 0)).toFixed(2)),
                "totalPagar": parseFloat((sale.totalWithDiscount).toFixed(2)),
                "totalLetras": NumeroALetras(parseFloat((sale.totalWithDiscount).toFixed(2))),
                "saldoFavor": 0.00,
                "condicionOperacion": 1,
                "pagos": [
                    {
                        "codigo": sale.paymentMethodDetail.paymentMethod.codeMH,
                        "montoPago":parseFloat((sale.totalWithDiscount).toFixed(2)),
                        "referencia": `${sale.paymentMethodDetail.paymentMethod.paymentMethodName}`,
                        "plazo": null,
                        "periodo": null
                    }
                ],
                "numPagoElectronico": null
            },
            "extension": null,
            "apendice": null
        }

    } catch (error) {
        console.log(error);
        return error;
    }
}

//function to create dte for credit note
export const dteNcr = async (id) => {
    try {
        const sale = await Sales.findOne({
            where:{
                saleID:id,
            },
            include:[
                {model:SaleDetails, 
                    include:[
                    {model:Buttons},
                    {model:Modifiers},
                    ]
                },
                {model:PaymentMethodDetails,
                    include:[{model:PaymentMethods}]
                }
            ]
        });
        
        const emisor = await dteEmisor("05");
        const receptor = {
            "nit": "06142307091063",
            "nrc": "1966072",
            "nombre": "Osmaro Bonilla",
            "codActividad": "56210",
            "descActividad": "Servicios de comidas y bebidas",
            "nombreComercial": null,
            "direccion": {
                "departamento": "06",
                "municipio": "01",
                "complemento": "La Gloria"
            },
            "telefono": null,
            "correo": "osmaro.bonilla.skysof@gmail.com"
        };

        const dteBody = [{
            "numItem": 1,
            "tipoItem": 1,
            "numeroDocumento": sale.dteGenerationCode,
            "cantidad": 1,
            "codigo": "B00004",
            "codTributo": null,
            "uniMedida": 59,
            "descripcion": "SUB del día",
            "precioUni": 0.50,
            "montoDescu": 0,
            "ventaNoSuj": 0.00,
            "ventaExenta": 0.00,
            "ventaGravada": 0.50,
            "tributos": null,
        }];

        const apiCredential = await ApiCredential.findOne({ attributes: ['sandBox'], where: { apiCode: 'MH_FE' } });

        return {
            "identificacion": {
                "version": 3,
                "ambiente": apiCredential.sandBox == 1 ? '00' : '01',
                "tipoDte": "05",
                "numeroControl": `DTE-05-00500001-${sale.saleID.toString().padStart(15, '0')}`,
                "codigoGeneracion": crypto.randomUUID().toUpperCase(),
                // 1:previo - 2:diferido
                "tipoModelo": 1,
                // 1:normal - 2:contingencia
                "tipoOperacion": 1,
                "tipoContingencia": null,
                "motivoContin": null,
                "fecEmi": (new Date()).toISOString().split("T")[0],
                "horEmi": moment().format("HH:mm:ss"),
                "tipoMoneda": "USD"
            },
            "documentoRelacionado": [
                {
                    "tipoDocumento": "03",
                    "tipoGeneracion": 2,
                    "numeroDocumento": sale.dteGenerationCode,
                    "fechaEmision": sale.dateCreated,
                }
            ],
            "emisor": emisor,
            "receptor": receptor,
            "ventaTercero": null,
            "cuerpoDocumento": dteBody,
            "resumen": {
                "totalNoSuj": 0,
                "totalExenta": 0,
                "totalGravada": 0.50,
                "subTotalVentas": 0.50,
                "descuNoSuj": 0.00,
                "descuExenta": 0.00,
                "descuGravada": 0,
                "totalDescu": 0,
                "tributos": null,
                "subTotal": 0.50,
                "ivaPerci1": 0.00,
                "ivaRete1": 0.00,
                "reteRenta": 0.00,
                "montoTotalOperacion": 0.50,
                "totalLetras": NumeroALetras(0.50),
                "condicionOperacion": 1,
            },
            "extension": null,
            "apendice": null
        }


    } catch (error) {
        console.log(error);
        return error;
    }
}

//function to create dte for CR (Comprobante de Retencion)
export const dteCr = async (id) => {
    try {
        const sale = await Sales.findOne({
            where:{
                saleID:id,
            },
            include:[
                {model:SaleDetails, 
                    include:[
                    {model:Buttons},
                    {model:Modifiers},
                    ]
                },
                {model:PaymentMethodDetails,
                    include:[{model:PaymentMethods}]
                }
            ]
        });
        
        const emisor = await dteEmisor("07");
        const receptor = {
            "tipoDocumento": "13",
            "numDocumento": "05908844-5",
            "nrc": null,
            "nombre": "Gerardo Palacios",
            "codActividad": '56210',
            "descActividad": "Servicios de comidas y bebidas",
            "nombreComercial": null,
            "direccion": {
                "departamento": "06",
                "municipio": "12",
                "complemento": "Calle Las Águilas"
            },
            "telefono": null,
            "correo": "gpalacios@gmail.com"
        };

        const dteBody = [
            {
                "numItem": 1,
                "tipoDte": "03",
                "tipoDoc": 1,
                "numDocumento": "1560938D-0A76-4458-B3C4-46A3CF8D5F15",
                "fechaEmision": "2024-01-31",
                "montoSujetoGrav": 100,
                "codigoRetencionMH": "C4",
                "ivaRetenido": 13,
                "descripcion": "Retencion de IVA",

            },
            {
                "numItem": 2,
                "tipoDte": "03",
                "tipoDoc": 1,
                "numDocumento": "EDDED579-7853-45BF-AC1A-654133D665CA",
                "fechaEmision": "2024-01-31",
                "montoSujetoGrav": 200,
                "codigoRetencionMH": "C4",
                "ivaRetenido": 26,
                "descripcion": "Retencion de IVA",
            }
        ];

        const apiCredential = await ApiCredential.findOne({ attributes: ['sandBox'], where: { apiCode: 'MH_FE' } });

        return {
            "identificacion": {
                "version": 1,
                "ambiente": apiCredential.sandBox == 1 ? '00' : '01',
                "tipoDte": "07",
                "numeroControl": `DTE-07-00500001-${sale.saleID.toString().padStart(15, '0')}`,
                "codigoGeneracion": crypto.randomUUID().toUpperCase(),
                // 1:previo - 2:diferido
                "tipoModelo": 1,
                // 1:normal - 2:contingencia
                "tipoOperacion": 1,
                "tipoContingencia": null,
                "motivoContin": null,
                "fecEmi": (new Date()).toISOString().split("T")[0],
                "horEmi": moment().format("HH:mm:ss"),
                "tipoMoneda": "USD"
            },
            "emisor": emisor,
            "receptor": receptor,
            "cuerpoDocumento": dteBody,
            "resumen": {
                "totalSujetoRetencion": 300,
                "totalIVAretenido": 39,
                "totalIVAretenidoLetras": "TREINTA Y NUEVE DOLARES CON 00/100",
            },
            "extension": null,
            "apendice": null
        }

    } catch (error) {
        console.log(error);
        return error;
    }
}
// function to create dte for FSE
export const dteFse = async (id,number) => {
    const sales = await Sales.findOne({
        where:{
            saleID:id,
        },
        include:[
            {model:SaleDetails, 
                include:[
                {model:Buttons},
                {model:Modifiers},
                ]
            },
            {model:PaymentMethodDetails,
                include:[{model:PaymentMethods}]
            },{model:Customers,
                include:[{model:Municipios,
                    include:{model:Departamentos}
                }]
            }
        ]
    });

    const apiCredential = await ApiCredential.findOne({ attributes: ['sandBox'], where: { apiCode: 'MH_FE' } });

    const identificacion = {
        "version": 1,
        "ambiente": apiCredential.sandBox == 1 ? '00' : '01',
        "tipoDte": "14",
        // retorna despues de enviar el json al ministerio
        "numeroControl": `DTE-14-00500001-0000000000000${number}`,
        // hay que crear el codigo de generacion
        "codigoGeneracion": crypto.randomUUID().toUpperCase(),
        // modelo previo
        "tipoModelo": 1,
        // 1:normal - 2:contingencia
        "tipoOperacion": 1,
        "tipoContingencia": null,
        "motivoContin": null,
        "fecEmi": sales.dateCreated,
        "horEmi": sales.hourCreated,
        "tipoMoneda": "USD"
    };
    const ticketConfig = await TiketConfiguration.findOne({attributes: ["nit", "nrc", "item", "enterprise", "departamentoMH", "municipioMH", "address", "phone", "email"]});
    const emisor = {
        "nit": ticketConfig.nit.trim().replace(/-/g, ''),
        "nrc": ticketConfig.nrc.trim().replace(/-/g, ''),
        "descActividad": ticketConfig.item,
        "codActividad": ticketConfig.activityCodeMH,
        "nombre": ticketConfig.enterprise,
        "direccion": {
            "departamento": ticketConfig.departamentoMH,
            "municipio": ticketConfig.municipioMH,
            "complemento": ticketConfig.address
        },
        "telefono": ticketConfig.phone,
        "correo": ticketConfig.email,
        "codEstableMH":null,
        "codEstable":null,
        "codPuntoVentaMH":null,
        "codPuntoVenta":null
    }
    let sujetoExcluido = {
        "tipoDocumento": sales.customer.documentType,
        "numDocumento": sales.customer.customerDoc.trim().replace(/-/g, ''),
        "nombre": sales.customer.customerName,
        "codActividad": sales.customer.activityCode,
        "descActividad": sales.customer.activity,
        "direccion":{
            "departamento": sales.customer?.municipio?.departamento?.codeMH,
            "municipio": sales?.customer?.municipio?.codeMH,
            "complemento": sales.customer.address == null ? 'El Salvador C.A' : sales.customer.address
        },
        "telefono": sales.customer.tel,
        "correo": sales.customer.email
    };
    const facBody = sales.saleDetails.map((saleDetail) => {
        return {
            "numItem": saleDetail.line,
            "tipoItem": 1,
            "cantidad": parseFloat((saleDetail.cant).toFixed(2)),
            "codigo": saleDetail.itemCode,
            "uniMedida": 59,
            "descripcion": [saleDetail.button && saleDetail.button.buttonName, saleDetail.modifier && saleDetail.modifier.modifierName].find(name => name != null),
            "precioUni": parseFloat((saleDetail.price).toFixed(4)),
            "montoDescu": parseFloat((saleDetail.discountLine).toFixed(4)),
            "compra": parseFloat((saleDetail.totalWithDiscount).toFixed(4)),
        }
    }).sort((a, b) => a.numItem - b.numItem)
    const resumen = {
        "totalCompra": parseFloat((sales.totalWithTax).toFixed(2)),
        "descu":parseFloat((sales.totalDiscount).toFixed(2)),
        "totalDescu":parseFloat((sales.totalDiscount).toFixed(2)),
        "subTotal": parseFloat((sales.totalWithTax).toFixed(2)),
        "ivaRete1": 0.00,
        "reteRenta":0.00,
        "totalPagar": parseFloat((sales.totalWithDiscount).toFixed(2)),
        "totalLetras": NumeroALetras(parseFloat((sales.totalWithDiscount).toFixed(2))),
        "condicionOperacion": 1,
        "pagos": [
            {
                "montoPago":parseFloat((sales.totalWithDiscount).toFixed(2)),
                "codigo": sales.paymentMethodDetail.paymentMethod.codeMH,
                "referencia": null,
                "plazo": null,
                "periodo": null
            }
        ],
        "observaciones":null,
    }

    // const options = {
    //     headers: {
    //         "content-type": "application/json",
    //         'Access-Control-Allow-Origin': '*',
    //         'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE,PATCH,OPTIONS',
    //     }
    // };
    // const data = {
    //     "nit": ticketConfig.nit.trim().replace(/-/g, ''),
    //     "activo": true,
    //     "passwordPri": MH_SIGNER_PASS,
    //     "dteJson": {
    //         "identificacion":identificacion,
    //         "emisor":emisor,
    //         "sujetoExcluido":sujetoExcluido,
    //         "cuerpoDocumento":facBody,
    //         "resumen":resumen,
    //         "apendice": null
    //     }
    // }

    // const dataSigned = await axios.post(MH_SIGNER_URL, data, options);

    
    // const optionsMH = {
    //     timeout: 20000,
    //     headers: {
    //       "content-type": "application/json",
    //       'Authorization': "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIwNjE0MTMwOTEwMTA1MSIsImF1dGhvcml0aWVzIjpbIlVTRVIiLCJVU0VSX0FQSSIsIlVzdWFyaW8iXSwiaWF0IjoxNzA2ODA2ODcwLCJleHAiOjE3MDY4OTMyNzB9.T5c3EKEUl-sze35jTNGKmhMxYTz7nc58OXJFHXqU-a_qdBs9bZl0QQGJ0xTAuBMLpsu3Gx_AwWTBSwS7oPRhMw"
    //     }
    //   };

    //   const respuestaHacienda = await axios.post(MH_FE_URL + "/recepciondte",{
    //     "ambiente": "00",
    //     "idEnvio": 1,
    //     "version": 1,
    //     "tipoDte": '14',
    //     "documento": dataSigned.data.body
    //   }, optionsMH);
      
    //   console.log(respuestaHacienda);


    return data;
}

//function to create invalidation dte
export const dteInvalidation = async (id, applicant) => {
    try {
        const sale = await Sales.findOne({
            where:{
                saleID: id,
            },
            include:[
                { model:SaleDetails, include:[ {model:Buttons}, {model:Modifiers} ] },
                { model:PaymentMethodDetails, include:[{model:PaymentMethods}] },
                { model: Correlatives },
                {
                    model: Customers,
                    include:[{ model: Municipios, include: { model:Departamentos } }]
                }
            ]
        });
        
        const emisor = await dteEmisor("anulacion");

        //creating customer object
        const receptor = {
            tipoDocumento: null,
            numDocumento: null,
            nombre: sale.client || null,
            telefono: null,
            correo: null
        };

        if (sale.customer) {
            receptor.tipoDocumento = sale.customer.documentType;
            receptor.numDocumento = sale.customer.documentType == '13' ? sale.customer.customerDoc : sale.customer.customerDoc.trim().replace(/-/g, '');
            receptor.nombre = sale.customer.customerName ? sale.customer.customerName : sale.customer.comercialName;
            receptor.telefono = sale.customer.tel ? sale.customer.tel : null;
            receptor.correo = sale.customer.email;
        }

        //getting info from the manager "gerente"
        const gerente = await User.findOne({ 
            include: [
                { model: Employee, attributes: ["employeeName", "employeeLastName", "employeeCode"] },
            ],
            where: { roleID: 1 } 
        });

        const apiCredential = await ApiCredential.findOne({ attributes: ['sandBox'], where: { apiCode: 'MH_FE' } });

        return {
            "identificacion": {
                "version": 2,
                "ambiente": apiCredential.sandBox == 1 ? '00' : '01',
                "codigoGeneracion": crypto.randomUUID().toUpperCase(),
                "fecAnula": moment().format("YYYY-MM-DD"),
                "horAnula": moment().format("HH:mm:ss"),
            },
            "emisor": emisor,
            "documento": {
                "tipoDte": sale.correlative.codeMH,
                "codigoGeneracion": sale.dteGenerationCode,
                "selloRecibido": sale.dteReceivedStamp,
                "numeroControl": sale.dteControlNumber,
                "fecEmi": sale.dateCreated,
                "montoIva": sale.totalTax,
                "codigoGeneracionR": null,
                ...receptor
            },
            "motivo": {
                "tipoAnulacion": 2,
                "motivoAnulacion": null,
                "nombreResponsable": gerente.employee.employeeName + " " + gerente.employee.employeeLastName,
                "tipDocResponsable": "37",
                "numDocResponsable": gerente.employee.employeeCode || "00001",
                "nombreSolicita": applicant.name,
                "tipDocSolicita": applicant.docType,
                "numDocSolicita": applicant.docNumber,
            }
        }
    } catch (error) {
        console.log(error);
        return error;
    }
}

export const dteSign = async (dte) => {
    const options = {
        headers: {
            "content-type": "application/json",
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE,PATCH,OPTIONS',
        }
    };

    //getting nit from sequelize
    const apiCredential = await ApiCredential.findOne({where: { apiCode: 'MH_SIGNER' }});
    apiCredential.apiResponse
    const ticketConfig = await TiketConfiguration.findOne({attributes: ["nit"]});

    const data = {
        "nit": ticketConfig.nit.trim().replace(/-/g, ''),
        "activo": true,
        "passwordPri": apiCredential.password,
        "dteJson": dte
    }

    const dataSigned = await axios.post(apiCredential.apiUrl, data, options);

    return dataSigned.data.body;
}

export const sendEmailRD = async (dte) => {
    const options = {
        headers: {
            "content-type": "application/json",
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
        },
        timeout: 10000
    };

 
    const data = {
        dte
    }
    
    const apiCredential = await ApiCredential.findOne({where:{apiCode:'EMAIL_API'}})
    const response = await axios.post(`${apiCredential.apiUrl}/send-email`, data, options);
    return response.data;
}

export const sendEmail = async (dte, anulacionData) => {
    const options = {
        headers: {
            "content-type": "application/json",
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
        },
        timeout: 10000
    };

    // Only set selloRecepcion if anulacionData is not provided
    if(!anulacionData) {
        dte.identificacion.selloRecepcion = dte?.respuestaHacienda?.selloRecibido;
    }
 
    const data = {
        dte,
        anulacionData
    }
    
    const apiCredential = await ApiCredential.findOne({where:{apiCode:'EMAIL_API'}})
    const response = await axios.post(`${apiCredential.apiUrl}/send-email`, data, options);
    return response.data;
}


//general functions
async function dteEmisor(tipoDocumento = "01") {
    const ticketConfig = await TiketConfiguration.findOne({attributes: ["nit", "nrc", "item", "enterprise", "departamentoMH", "municipioMH", "address", "phone", "email", "codEstablecimientoMH", "codPosMH", "comercialName", "activityCodeMH"]});
    const emisor = {
        "nit": ticketConfig.nit.trim().replace(/-/g, ''),
        "nrc": ticketConfig.nrc.trim().replace(/-/g, ''),
        "descActividad": ticketConfig.item,
        "codActividad": ticketConfig.activityCodeMH,
        "nombre": ticketConfig.enterprise,
        "nombreComercial": ticketConfig.comercialName,
        "tipoEstablecimiento":"01",
        "direccion": {
            "departamento": ticketConfig.departamentoMH,
            "municipio": ticketConfig.municipioMH,
            "complemento": ticketConfig.address
        },
        "telefono": ticketConfig.phone,
        "correo": ticketConfig.email,
    }

    if (["01", "03", "14"].includes(tipoDocumento)) {
        emisor.codEstableMH = ticketConfig.codEstablecimientoMH;
        emisor.codEstable = null;
        emisor.codPuntoVentaMH = ticketConfig.codPosMH;
        emisor.codPuntoVenta = null;
    }

    if (["07"].includes(tipoDocumento)) {
        emisor.codigoMH = null;
        emisor.codigo = null;
        emisor.puntoVentaMH = null;
        emisor.puntoVenta = null;
    }

    if (tipoDocumento == "anulacion") {
        emisor.nomEstablecimiento = "SUBYWAY";
        emisor.codEstable = ticketConfig.codEstablecimientoMH;
        emisor.codPuntoVenta = ticketConfig.codPosMH;
        delete emisor.descActividad;
        delete emisor.codActividad;
        delete emisor.direccion;
        delete emisor.nombreComercial;
        delete emisor.nrc;
    }

    return emisor;
}