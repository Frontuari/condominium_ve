// Copyright (c) 2022, Armando Rojas and contributors
// For license information, please see license.txt

frappe.ui.form.on("Condominium Common Expenses", {
  refresh: function (frm) {
    
    if (!frm.doc.docstatus || frm.doc.docstatus == 0) {
      frm.add_custom_button(__("Search"), () => {
        if (frm.doc.posting_date && frm.doc.condominium) {
          
          
          frappe.call({
            method:
              "condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.get_invoice_condo",
            args: {
              condo: frm.doc.condominium,
              date: frm.doc.posting_date,
              excluded_sectors: get_excluded_sectors_name(frm),
            },

            btn: $(".primary-action"),

            freeze: true,
            callback: (response) => {
              //let fecha_doc = new Date(frm.doc.posting_date+' 23:59:00')

              let data = response.data;

              // retirar el monto del fondo del monto total
              /*
              for (var k = 0; k < data.creation_funds_date.length; k++) {
                  if (fecha_doc < new Date(data.creation_funds_date[k].creation) ){
                    
                    for (var j = 0; j < data.funds.length; j++) {
                      if (data.funds[j].concept == data.creation_funds_date[k].description ){
                        data.total -= data.funds[j].amount;
                      }
                    }

                  }
              }

              data.total_per_unit = data.total / data.active_units
              */
              frm.set_value("condominium_common_expenses_invoices", []);
              frm.set_value("condominium_common_expenses_detail", []);
              frm.set_value("detail_funds", []);
              frm.set_value("funds", []);
              frm.set_value("expense", []);

              frm.doc.total_per_unit = data.total_per_unit;
              frm.doc.total = data.total;
              frm.doc.active_units = data.active_units;

              frm.doc.funds_current = data.funds_current_total;
              frm.doc.funds_expenditure = data.funds_expenditure_total;
              frm.doc.funds_received = data.funds_receive_total;
              frm.doc.previous_funds = data.previous_funds;



              data.invoices.forEach((e) => {
                frm.add_child("condominium_common_expenses_invoices", {
                  invoice: e.invoice,
                  date: e.date,
                  supplier: e.supplier,
                  amount: e.amount,
                });
              });

              data.detail.forEach((e) => {
                frm.add_child("condominium_common_expenses_detail", {
                  concept: e.concept,
                  supplier: e.supplier,
                  per_unit: e.per_unit,
                  amount: e.amount,
                  tax: e.tax,
                  net: e.net,
                  parent_concept: e.parent_cost_center,
                });
              });
              
              

              data.expense_funds.forEach((e) => {
                
                let fecha_fondo_valida = true;
                /*for (var i = 0; i < data.creation_funds_date.length; i++) {
                  if (fecha_doc >= new Date(data.creation_funds_date[i].creation) ){
                    fecha_fondo_valida = true
                  }
                }
                */
                if (fecha_fondo_valida){
                  frm.add_child("expense", {
                    concept: e.concept,
                    supplier: e.supplier,
                    per_unit: e.per_unit,
                    amount: e.amount,
                    tax: e.tax,
                    net: e.net,
                    parent_concept: e.parent_cost_center,
                  });
                }
              });


              
              
              data.funds.forEach((e) => {
                let fecha_fondo_valida = true;
                /*
                for (var i = 0; i < data.creation_funds_date.length; i++) {
                  if (fecha_doc >= new Date(data.creation_funds_date[i].creation) ){
                    fecha_fondo_valida = true
                  }
                }
                */
                if (fecha_fondo_valida){
                frm.add_child("funds", {
                    amount: e.amount,
                    amount_per_unit: e.amount_per_unit,
                    account: e.account,
                    concept: e.concept,
                  });
                }
              });



              data.detail_funds_use.forEach((e) => {
                let fecha_fondo_valida = true;
                /*
                for (var i = 0; i < data.creation_funds_date.length; i++) {
                  if (fecha_doc >= new Date(data.creation_funds_date[i].creation) ){
                    fecha_fondo_valida = true
                  }
                }*/

                if (fecha_fondo_valida){
                  frm.add_child("detail_funds", {
                    concept: e.concept,
                    funds_current: e.funds_current,
                    funds_receive: e.funds_receive,
                    previous_funds: e.previous_funds,
                    funds_expenditure: e.funds_expenditure
                  });
                }
              });


              frm.refresh_field("condominium_common_expenses_invoices");
              frm.refresh_field("condominium_common_expenses_detail");

              frm.refresh_field("total_per_unit");
              frm.refresh_field("funds");
              frm.refresh_field("total");
              frm.refresh_field("expense");
              frm.refresh_field("active_units");

              frm.refresh_field("funds_current");
              frm.refresh_field("funds_expenditure");
              frm.refresh_field("funds_received");
              frm.refresh_field("previous_funds");

              frm.refresh_field("detail_funds");


            },

            error: (r) => {
              console.log(r);
            },
          });
        }
      });
    } else {
      frm.remove_custom_button(__("Search"));

      frm.page.add_menu_item(__("Enviar Correos"), () => {

          
          frappe.call({
            method:
              "condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.send_email_test",
            args: {
              ggc: frm.doc.name,
              excluded_sectors: frm.doc.excluded_sectors
            },

            btn: $(".primary-action"),

            freeze: true,
            callback: (response) => {

            },

            error: (r) => {
              console.log(r);
            },
          });

      });

      // agrega o elimina el boton para generar las facturas faltantes
      btn_gen_missing_invoices(frm);

      // agregar o eliminar el boton para validar los recibos de condominio
      btn_validate_documents(frm);
      
    }
  },

  before_save: function(frm){
    let active_units = frm.doc.active_units;
    // calculo de costos en caso de sectores excluidos
    
    if (frm.doc.excluded_sectors && frm.doc.excluded_sectors.length > 0){
      
      frappe.call({
        method:
          "condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.get_active_house_sectors",
        args: {
          excluded_sectors: frm.doc.excluded_sectors
        },

        //btn: $(".primary-action"),

        freeze: true,
        callback: (response) => {
          frm.doc.active_units = response.data;
          active_units = response.data;

          let total = 0;
          for (var i = 0; i < frm.doc.condominium_common_expenses_detail.length; i++) {
            total += frm.doc.condominium_common_expenses_detail[i].amount;
            frm.doc.condominium_common_expenses_detail[i].per_unit = frm.doc.condominium_common_expenses_detail[i].amount / active_units;
          }

          if (frm.doc.funds){
            for (var i = 0; i < frm.doc.funds.length; i++) {
              total += frm.doc.funds[i].amount;
            }
          }

          frm.doc.total = total;
          frm.doc.total_per_unit = total / active_units;


        }
      });
      
    }else{

      let total = 0;
      for (var i = 0; i < frm.doc.condominium_common_expenses_detail.length; i++) {
        total += frm.doc.condominium_common_expenses_detail[i].amount;
        frm.doc.condominium_common_expenses_detail[i].per_unit = frm.doc.condominium_common_expenses_detail[i].amount / active_units;
      }

      if (frm.doc.funds){
        for (var i = 0; i < frm.doc.funds.length; i++) {
          total += frm.doc.funds[i].amount;
        }
      }

      frm.doc.total = total;
      frm.doc.total_per_unit = total / active_units;
      }

  },

  caculate_funds(frm){

    let data = frm.doc 
    
    let total = parseFloat(data.funds_received )-  parseFloat(data.funds_expenditure )+ parseFloat(data.previous_funds)

    frm.set_value("funds_current", total);
    frm.refresh_field("detail_funds");
  },

  caculate_funds_detail(frm){

    let data = frm.doc 

    data.funds_received  = 0
    data.funds_expenditure  = 0
    data.previous_funds  = 0
    data.funds_current  = 0


    console.log(data)

    data.detail_funds.forEach(ddf =>{

      data.funds_received  += parseFloat(ddf.funds_receive)
      data.funds_expenditure  += parseFloat(ddf.funds_expenditure)
      data.previous_funds  += parseFloat(ddf.previous_funds)
      data.funds_current  += parseFloat(ddf.funds_current)

    })

    let total = parseFloat(data.funds_received )-  parseFloat(data.funds_expenditure )+ parseFloat(data.previous_funds)

    frm.set_value("funds_current", total);

    frm.refresh_field("funds_received");
    frm.refresh_field("funds_expenditure");
    frm.refresh_field("previous_funds");
    frm.refresh_field("funds_current");
  },


  funds_received(frm){
    frm.events.caculate_funds(frm)
  },

  funds_expenditure(frm){
    frm.events.caculate_funds(frm)
  },

  previous_funds(frm){
    frm.events.caculate_funds(frm)
  },

  calculate_funds_detail(frm ,  cdt, cdn){
    let data = frappe.get_doc(cdt, cdn);

    
    let total = parseFloat(data.funds_receive )-  parseFloat(data.funds_expenditure )+ parseFloat(data.previous_funds)

    data.funds_current = total
    frm.refresh_field("detail_funds");
    
    frm.events.caculate_funds_detail(frm)
  },

  excluded_sectors(frm){
    let sectores = [];

    for (let i = 0; i < frm.doc.excluded_sectors.length; i++) {
      const element = frm.doc.excluded_sectors[i];
      if (element !== '')
        sectores.push(element.territory);
      
    }
    frm.set_query("excluded_sectors", function() {
      return {
        "filters": [
          ["Territory", "name", "in", frm.doc.platform]
        ]
      };
    });
  }
});

function btn_gen_missing_invoices(frm) {
  frappe.call({
    method: "condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.is_invoices_generated",
    args: {
      ggc: frm.doc.name,
      active_units: frm.doc.active_units,
      n_funds: frm.doc.funds.length
    },
    freeze: true,
    callback: (response) => {
      if (response.data && frm.doc.docstatus == 1){
        // agregar boton para crear facturas faltantes en caso de que no se hayan generado
        frm.add_custom_button(__("Generate Missing Invoices"), () => {
          frappe.confirm('Esta a punto de generar recibos de Cuentas por Cobrar a los propietarios que no lo posean, ¿Quiere proceder?',
            () => {
                // si es yes genera las facturas faltantes
                generate_missing_invoices(frm, frm.doc.name, frm.doc.excluded_sectors);
            });
        });
      }
    },
    error: (r) => {
      console.log(r);
    }
  });
}

function btn_validate_documents(frm) {
  frappe.call({
    method: "condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.get_total_draft_doc",
    args: {
      gcc: frm.doc.name
    },
    freeze: true,
    callback: (response) => {
      if (response.total_doc && response.total_doc > 0 && frm.doc.docstatus == 1){

        // agregar boton para validar los recibos de condominio
        frm.add_custom_button(__("Validate Receipts"), () => {
          frappe.confirm('Esta a punto de validar los recibos de condominio, ¿Quiere proceder?',
            () => {
                // si es yes genera las facturas faltantes
                validate_receipts_doc(frm);
            });
        });
        frm.change_custom_button_type(__("Validate Receipts"), null, 'primary');
      }
    },
    error: (r) => {
      console.log(r);
    }
  });
}


function generate_missing_invoices(frm, docname, excluded_sectors){
  frappe.call({
    method:
      "condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.gen_missing_invoices",
    args: {
      ggc: docname,
      excluded_sectors: excluded_sectors
    },

    //btn: $(".primary-action"),

    freeze: true,
    callback: (response) => {
      frm.refresh();
    },
    error: (r) => {
      console.log(r);
    }
  });
}

function validate_receipts_doc(frm){
  frappe.call({
    method:
      "condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.validate_recipts_doc",
    args: {
      gcc: frm.doc.name,
    },

    btn: $(".primary-action"),

    freeze: true,
    callback: (response) => {
      frm.refresh()
    },
    error: (r) => {
      console.log(r);
    }
  });
}

function get_excluded_sectors_name(frm){
  var excluded_sectors = [];
  if (frm.doc.excluded_sectors) {
    frm.doc.excluded_sectors.forEach(element => {
      if (element.hasOwnProperty("territory"))
        excluded_sectors.push(element.territory);
    });
  }
  return excluded_sectors;
}

frappe.ui.form.on("Detail Funds", {

  funds_receive(frm, cdt, cdn) {
   
    
    frm.events.calculate_funds_detail(frm , cdt,cdn)

  },

  funds_expenditure(frm, cdt, cdn) {
   
    
    frm.events.calculate_funds_detail(frm , cdt,cdn)

  },

  previous_funds(frm, cdt, cdn) {
   
    
    frm.events.calculate_funds_detail(frm , cdt,cdn)

  },
 
  
});


frappe.ui.form.on("Condo Exclude Sector",{

  excluded_sectors_add(frm, cdt, cdn){
    // agregar filtro para que solo muestre los sectores que aun no estan excluidos en el campo de enlace
    let sectores = [];

    for (let i = 0; i < frm.doc.excluded_sectors.length; i++) {
      const element = frm.doc.excluded_sectors[i];
      if (element.territory !== '' && element.territory)
        sectores.push(element.territory);
      
    } 
    frm.set_query("territory", 'excluded_sectors', () => {
      return {
        filters: {
          name:["not in", sectores],
          is_group: 0,
          parent_territory: ["!=", "Todos los territorios"]
        }
      };
    });
  }
  
});


