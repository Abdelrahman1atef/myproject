# # api/views.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from django.db import connection
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
import json
from rest_framework import status
from .models import Product, ProductAmount, SalesHeader, SalesDetails, GedoFinancial, CashDepots
from .serializers import ProductSerializer, ProductAmountSerializer, SalesHeaderSerializer, SalesDetailsSerializer, GedoFinancialSerializer, CashDepotsSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
import logging

def home(request):
    return render(request, 'api/api_list.html')

class ProductListView(APIView):
    def get(self, request):
        # Get the page number from the request
        page_number = request.query_params.get('page', 1)

        # Generate a unique cache key for this page
        cache_key = f'product_list_page_{page_number}'
        # print("Cache key:", cache_key)  # Debugging

        # Check if the paginated data is cached
        cached_data = cache.get(cache_key)
        if cached_data:
            # print("Serving from cache:", cached_data)  # Debugging
            return Response(cached_data)

        # Define the raw SQL query
        query = """
            SELECT 
                p.product_id,
                p.product_code,
                p.product_name_ar,
                p.product_name_en,
                p.sell_price,
                ISNULL(
                    (SELECT CAST(SUM(pa.amount) AS INT) 
                     FROM Product_Amount pa
                     WHERE pa.product_id = p.product_id), 
                    0
                ) AS amount,
                p.product_image_url,
            	
                (
                    SELECT 
                        c.company_id,
                        c.co_name_en,
                        c.co_name_ar
                    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
                ) AS company,
                (
                    SELECT 
                        pg.group_id,
                        pg.group_name_en,
                        pg.group_name_ar
                    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
                ) AS product_group
                
            FROM 
                Products p
            LEFT JOIN 
                Product_groups pg ON p.group_id = pg.group_id
            LEFT JOIN 
                Companys c ON p.company_id = c.company_id
        """

        # Execute the raw SQL query
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]  # Get column names
            rows = cursor.fetchall()

        # Convert the rows into a list of dictionaries
        products = []
        for row in rows:
            product = dict(zip(columns, row))
            # Parse the nested JSON fields
            product['company'] = json.loads(product['company'])
            product['product_group'] = json.loads(product['product_group'])
            products.append(product)
        # print("Raw data from database:", products)  # Debugging

        # Set up pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(products, request)

        # Build the response data
        response_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": result_page,
        }
        # print("Response data before caching:", response_data)  # Debugging

        # Cache the entire response
        cache.set(cache_key, response_data, timeout=60 * 15)  # Cache for 15 minutes

        # Return the response
        return Response(response_data)

class ProductListByCompanyView(APIView):
    def get(self, request, company_id):
        page_number = request.query_params.get('page', 1)
        cache_key = f'product_list_company_{company_id}_page_{page_number}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)
        query = f"""
            {query_head}
    WHERE p.company_id = {company_id}
"""

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        products = []
        for row in rows:
            product = dict(zip(columns, row))
            product['company'] = json.loads(product['company']) if product['company'] else None
            product['product_group'] = json.loads(product['product_group']) if product['product_group'] else None
            products.append(product)

        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(products, request)

        response_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": result_page,
        }

        cache.set(cache_key, response_data, timeout=60 * 15)
        return Response(response_data)

class ProductListByGroupView(APIView):
    def get(self, request, group_id):
        page_number = request.query_params.get('page', 1)
        cache_key = f'product_list_group_{group_id}_page_{page_number}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        query = f"""
            {query_head}
            WHERE p.group_id = {group_id}
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        products = []
        for row in rows:
            product = dict(zip(columns, row))
            product['company'] = json.loads(product['company']) if product['company'] else None
            product['product_group'] = json.loads(product['product_group']) if product['product_group'] else None
            products.append(product)

        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(products, request)

        response_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": result_page,
        }

        cache.set(cache_key, response_data, timeout=60 * 15)
        return Response(response_data)

class ProductDetailView(APIView):
    def get(self, request, product_id):
        query = f"""
            {query_head}
            WHERE p.product_id = {product_id}
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()

        if row is None:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        product = dict(zip(columns, row))
        product['company'] = json.loads(product['company']) if product['company'] else None
        product['product_group'] = json.loads(product['product_group']) if product['product_group'] else None

        return Response(product)

# View to retrieve stock levels for a product
class ProductStockView(APIView):
    def get(self, request, product_id, store_id):
        try:
            stock = ProductAmount.objects.filter(product_id=product_id, store_id=store_id)
            serializer = ProductAmountSerializer(stock, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# View to create a new sale


# Configure logging
logger = logging.getLogger(__name__)

class CreateSaleView(APIView):
    def post(self, request):
        # Extract data from request
        product_id = int(request.data.get('product_id', 0))  # Ensure integer
        store_id = int(request.data.get('store_id', 0))      # Ensure integer
        counter_id = float(request.data.get('counter_id', 0))  # Ensure float
        quantity = int(request.data.get('quantity', 0))      # Ensure integer

        try:
            # Step 1: Check if the product exists and has sufficient stock
            product_amount = get_product_amount(product_id, store_id, counter_id)

            if not product_amount:
                return Response({"error": "Product not found or insufficient stock"}, status=status.HTTP_400_BAD_REQUEST)

            if product_amount["amount"] < quantity:
                return Response({"error": "Insufficient stock"}, status=status.HTTP_400_BAD_REQUEST)

            # Deduct stock
            deduct_stock(product_id, store_id, counter_id, quantity)

            # Step 2: Create financial transaction in Gedo_Financial
            gf_data = {
                "gf_gedo_type": 7,  # Assuming this is for sales
                "gf_value": get_sell_price(product_id) * quantity,
                "gf_from_type": 10,  # Inventory
                "gf_to_type": 1,    # Cash
                "gf_notes": f"Sale of {quantity} units of product {product_id}",
                "gf_computer": "API_SERVER",
                "gf_actual_cashier": "API_USER",
                "gf_form_type": 11,
                "insert_uid": "API_USER",
            }
            gedo_financial = GedoFinancial.objects.create(**gf_data)

            # Step 3: Create sale header in Sales_Header
            sales_header_data = {
                "store_id": store_id,
                "customer_id": 0,  # Assuming no customer for now
                "class_type": "0",  # Normal sale
                "product_number": 1,
                "bill_money_befor": get_sell_price(product_id) * quantity,
                "total_bill": get_sell_price(product_id) * quantity,
                "gf_id": gedo_financial.gf_id,
                "insert_uid": "API_USER",
            }
            sales_header = SalesHeader.objects.create(**sales_header_data)

            # Step 4: Create sale detail in Sales_Details using raw SQL
            create_sales_detail(
                sales_id=sales_header.sales_id,
                product_id=product_id,
                counter_id=counter_id,
                quantity=quantity,
                sell_price=get_sell_price(product_id),
                buy_price=product_amount["buy_price"]
            )

            # Return success response
            return Response({
                "message": "Sale created successfully",
                "sales_id": sales_header.sales_id
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            logger.error(f"ValueError: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Helper function to fetch product amount
def get_product_amount(product_id, store_id, counter_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT product_id, store_id, counter_id, amount, buy_price
            FROM Product_Amount
            WHERE product_id = %s AND store_id = %s AND counter_id = %s
        """, [product_id, store_id, counter_id])

        result = cursor.fetchone()
        if result:
            return {
                "product_id": result[0],
                "store_id": result[1],
                "counter_id": result[2],
                "amount": result[3],
                "buy_price": result[4],
            }
        return None


# Helper function to get sell price
def get_sell_price(product_id):
    try:
        product = Product.objects.get(product_id=product_id)
        return product.sell_price
    except Product.DoesNotExist:
        raise ValueError("Product not found")


# Helper function to check stock
def check_stock(product_id, store_id, counter_id, quantity):
    product_amount = get_product_amount(product_id, store_id, counter_id)
    if product_amount and product_amount["amount"] >= quantity:
        return True
    return False


# Helper function to deduct stock
def deduct_stock(product_id, store_id, counter_id, quantity):
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE Product_Amount
            SET amount = amount - %s
            WHERE product_id = %s AND store_id = %s AND counter_id = %s
            AND amount >= %s
        """, [quantity, product_id, store_id, counter_id, quantity])

        if cursor.rowcount == 0:
            raise ValueError("Insufficient stock or product not found")


# Helper function to calculate the next details_id
def get_next_details_id(sales_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ISNULL(MAX(details_id), 0) + 1
            FROM Sales_details
            WHERE sales_id = %s
        """, [sales_id])
        result = cursor.fetchone()
        return result[0] if result else 1

def create_sales_detail(sales_id, product_id, counter_id, quantity, sell_price, buy_price):
    # Calculate the next details_id
    details_id = get_next_details_id(sales_id)

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Sales_details (
                details_id, sales_id, product_id, counter_id, amount, sale_unit_change, sale_unit, 
                sell_price, buy_price, disc_money, disc_per, total_sell, back, back_amount, 
                back_unit, back_gf_id, insert_uid, insert_date
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE()
            )
        """, [
            details_id, sales_id, product_id, counter_id, quantity, 1.0, 1,
            sell_price, buy_price, 0.0, 0.0, sell_price * quantity, "N", 0.0, 0, None, "API_USER"
        ])

        if cursor.rowcount == 0:
            raise ValueError("Failed to create sale detail")


query_head = """
           SELECT 
                p.product_id,
                p.product_code,
                p.product_name_ar,
                p.product_name_en,
                p.sell_price,
                ISNULL((
                    SELECT CAST(SUM(pa.amount) AS INT) 
                    FROM Product_Amount pa 
                    WHERE pa.product_id = p.product_id
                ), 0) AS amount,
                p.product_image_url,

                -- Get company details
                JSON_QUERY((
                    SELECT 
                        c.company_id,
                        c.co_name_en,
                        c.co_name_ar
                    FROM Companys c
                    WHERE c.company_id = p.company_id
                    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
                )) AS company,

                -- Get product group details
                JSON_QUERY((
                    SELECT 
                        pg.group_id,
                        pg.group_name_en,
                        pg.group_name_ar
                    FROM Product_groups pg
                    WHERE pg.group_id = p.group_id
                    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
                )) AS product_group
                

            FROM Products p
                """








