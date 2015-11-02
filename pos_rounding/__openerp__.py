{
    "name": "POS Round Off",
    "version": "8.0.0.1.0",
    "author": "Service Edge",
    "website": "http://www.servicedge.in",
    "license": "AGPL-3",
    "category": "Point Of Sale",
    "depends": ['base', 'point_of_sale'],
    'data': [
        #~ "views/pos_template.xml",
        "views/point_of_sale.xml",
        "point_of_sale_view.xml",
    ],
    "qweb": [
        'static/src/xml/pos.xml',
    ],
    'installable': True,
}
