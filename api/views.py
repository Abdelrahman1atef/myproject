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
from .models import Product
from .serializers import ProductSearchSerializer, UserProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import AppUserSerializer, LoginSerializer
from rest_framework.permissions import IsAuthenticated

def home(request):
    return render(request, 'api/api_list.html')

class CategoryView(APIView):   
    permission_classes = [AllowAny]
    def get(self, request):
        query = """
            select *
            from Product_Categories
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        groups = []
        for row in rows:
            group = dict(zip(columns, row))
            groups.append(group)

        return Response(groups)
    
class ProductSearchView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        # Get the search query from the URL parameter
        query = request.query_params.get('q', None)

        if query:
            cache_key = f"search_{query}"
            cached_results = cache.get(cache_key)
            if cached_results:
                return Response(cached_results, status=status.HTTP_200_OK)
            
            products = Product.objects.filter(
                Q(product_name_en__icontains=query) |
                Q(product_name_ar__icontains=query)
            )[:20]
            product = Product.objects.filter(product_name_en__icontains="test").first()
            serializer = ProductSearchSerializer(product)
            print(serializer.data)
            
            serializer = ProductSearchSerializer(products, many=True)
            cache.set(cache_key, serializer.data, timeout=60)  # Cache for 60 seconds
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)    
    
class ProductListView(APIView):
    permission_classes = [AllowAny]
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
                (
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit1
				)as product_unit1,
                p.sell_price,

				(
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit2
				)as product_unit2,
				p.product_unit1_2,
				p.unit2_sell_price,
				(
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit3
				)as product_unit3,
				p.product_unit1_3,
				p.unit3_sell_price,
				ISNULL(
                    (SELECT CAST(SUM(pa.amount) AS INT) 
                     FROM Product_Amount pa
                     WHERE pa.product_id = p.product_id), 
                    0
                ) AS amount,
                p.product_image_url,
                (
                select pd.pd_name_ar
                )as product_description,
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
                ) AS product_group,
                (
                    SELECT STRING_AGG(pi.image_url, ', ') -- Concatenate image URLs into a single string
                    FROM Product_Images pi
                    WHERE pi.product_id = p.product_id
                ) AS product_images -- Returns all image URLs as a comma-separated string
                
            FROM 
                Products p
            LEFT JOIN 
                Product_groups pg ON p.group_id = pg.group_id
            LEFT JOIN 
                Companys c ON p.company_id = c.company_id
            LEFT JOIN 
                Product_description pd on pd.pd_id=p.pd_id
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
            # Split the product_images string into a list of URLs
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []  # Empty list if no images exist
            
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
    permission_classes = [AllowAny]
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
            # Split the product_images string into a list of URLs
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []  # Empty list if no images exist
            
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
    permission_classes = [AllowAny]
    def get(self, request, group_id):
        page_number = request.query_params.get('page', 1)
        cache_key = f'product_list_group_{group_id}_page_{page_number}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        query = f"""
            {query_head}
            WHERE pg.category_id = {group_id}
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
            # Split the product_images string into a list of URLs
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []  # Empty list if no images exist
            
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
    permission_classes = [AllowAny]
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
        # Split the product_images string into a list of URLs
        if product['product_images']:
            product['product_images'] = product['product_images'].split(', ')
        else:
            product['product_images'] = []  # Empty list if no images exist
            
        return Response(product)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AppUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data  # This already has the correct full response.

        if user:
            return Response(user, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Token not found.'}, status=status.HTTP_400_BAD_REQUEST)



# # View to retrieve stock levels for a product
# class ProductStockView(APIView):
#     def get(self, request, product_id, store_id):
#         try:
#             stock = ProductAmount.objects.filter(product_id=product_id, store_id=store_id)
#             serializer = ProductAmountSerializer(stock, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# # View to create a new sale


# # Configure logging
# logger = logging.getLogger(__name__)

# class CreateSaleView(APIView):
#     def post(self, request):
#         # Check if the request body is a list (multi-product) or a single product
#         if isinstance(request.data, list):
#             return self.create_multi_product_sale(request.data)
#         else:
#             return self.create_single_product_sale(request.data)

#     def create_single_product_sale(self, data):
#         # Extract data from request
#         product_id = int(data.get('product_id', 0))  # Ensure integer
#         store_id = int(data.get('store_id', 0))      # Ensure integer
#         quantity = int(data.get('quantity', 0))      # Ensure integer

#         # Validate quantity
#         if quantity <= 0:
#             return Response({"error": "Quantity must be a positive integer"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Step 1: Check if the product exists and has sufficient stock across all counters
#             product_amount = get_total_product_amount(product_id, store_id)

#             if not product_amount["total_amount"]:
#                 return Response({
#                     "error": "Product not found or insufficient stock",
#                     "available_counters": product_amount["counter_stock"]
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             if product_amount["total_amount"] < quantity:
#                 return Response({
#                     "error": "Insufficient stock for product ID: {}".format(product_id),
#                     "available_counters": product_amount["counter_stock"]
#                 }, status=status.HTTP_400_BAD_REQUEST)

#                 # Step 2: Deduct stock from all counters where the product exists
#             counter_id = deduct_stock_from_all_counters(product_id, store_id, quantity)
   
#             # Step 3: Create the sale record in the Sales table
#             sales_id = create_sales_record(store_id, "API_USER")  # Helper function to create sales record
   
#             # Step 4: Create the sale detail in the Sales_details table
#             sell_price = get_sell_price(product_id)  # Helper function to fetch sell price
#             buy_price = get_buy_price(product_id)    # Helper function to fetch buy price
#             create_sales_detail(
#                 sales_id=sales_id,
#                 product_id=product_id,
#                 counter_id=counter_id,
#                 quantity=quantity,
#                 sell_price=sell_price,
#                 buy_price=buy_price
#             )
   
#             # Step 5: Return success response
#             return Response({
#                 "message": "Sale created successfully",
#                 "sales_id": sales_id,
#                 "product_id": product_id,
#                 "quantity": quantity,
#                 "counter_id": counter_id
#             }, status=status.HTTP_201_CREATED)
#             # Rest of the logic...
#         except ValueError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def create_multi_product_sale(self, data_list):
#      processed_products = []  # Track successfully processed products
#      failed_products = []     # Track products with issues
 
#      try:
#          with transaction.atomic():  # Ensure atomicity
#              # Validate stock for all products
#              for item in data_list:
#                  product_id = int(item.get('product_id', 0))
#                  store_id = int(item.get('store_id', 0))
#                  quantity = int(item.get('quantity', 0))
 
#                  if quantity <= 0:
#                      failed_products.append({"product_id": product_id, "reason": "Invalid quantity"})
#                      continue
 
#                  product_amount = get_total_product_amount(product_id, store_id)
#                  if not product_amount["total_amount"] or product_amount["total_amount"] < quantity:
#                      failed_products.append({
#                          "product_id": product_id,
#                          "reason": "Insufficient stock",
#                          "available_counters": product_amount["counter_stock"]
#                      })
#                      continue
 
#                  processed_products.append(item)
 
#              # If no products are processed, return an error
#              if not processed_products:
#                  return Response({"error": "No products could be processed", "failed_products": failed_products}, status=status.HTTP_400_BAD_REQUEST)
 
#              # Create a single sales header for processed products
#              total_quantity = sum(item['quantity'] for item in processed_products if 'quantity' in item and isinstance(item['quantity'], int))
#              total_bill = sum(get_sell_price(item['product_id']) * item['quantity'] for item in processed_products if 'product_id' in item)
 
#              sales_header_data = {
#                  "store_id": data_list[0].get('store_id', 0),
#                  "customer_id": 0,  # Assuming no customer for now
#                  "class_type": "0",  # Normal sale
#                  "product_number": len(processed_products),
#                  "bill_money_befor": float(total_bill),  # Convert Decimal to float
#                  "total_bill": float(total_bill),  # Convert Decimal to float
#                  "insert_uid": "API_USER",
#              }
#              sales_header = SalesHeader.objects.create(**sales_header_data)
 
#              # Process each product in the list
#              for item in processed_products:
#                  product_id = int(item.get('product_id', 0))
#                  store_id = int(item.get('store_id', 0))
#                  quantity = int(item.get('quantity', 0))
 
#                  # Deduct stock from all counters where the product exists
#                  counter_id = deduct_stock_from_all_counters(product_id, store_id, quantity)
 
#                  # Create sale detail
#                  create_sales_detail(
#                      sales_id=sales_header.sales_id,
#                      product_id=product_id,
#                      counter_id=counter_id,
#                      quantity=quantity,
#                      sell_price=float(get_sell_price(product_id)),  # Convert Decimal to float
#                      buy_price=float(product_amount["buy_price"])  # Convert Decimal to float
#                  )
 
#          # Return success response with details about processed and failed products
#          return Response({
#              "message": "Partial sale created successfully",
#              "sales_id": sales_header.sales_id,
#              "processed_products": [{"product_id": item['product_id'], "quantity": item['quantity']} for item in processed_products],
#              "failed_products": failed_products
#          }, status=status.HTTP_207_MULTI_STATUS)
 
#      except ValueError as e:
#          return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#      except Exception as e:
#          return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# # Helper function to fetch product amount
# def get_total_product_amount(product_id, store_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             SELECT product_id, store_id, SUM(amount) AS total_amount, MAX(buy_price) AS buy_price
#             FROM Product_Amount
#             WHERE product_id = %s AND store_id = %s
#             GROUP BY product_id, store_id
#         """, [product_id, store_id])

#         result = cursor.fetchone()
#         if result:
#             return {
#                 "product_id": result[0],
#                 "store_id": result[1],
#                 "total_amount": result[2],  # Total amount across all counters
#                 "buy_price":float(result[3]),  # Representative buy price
#                 "counter_stock": get_all_counter_stock(product_id, store_id)  # Include counter stock
#             }
#         return None

# # Helper function to get sell price
# def get_sell_price(product_id):
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT sell_price FROM Products WHERE product_id = %s", [product_id])
#         result = cursor.fetchone()
#         return float(result[0]) if result else 0.0
# def get_buy_price(product_id):
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT buy_price FROM Products WHERE product_id = %s", [product_id])
#         result = cursor.fetchone()
#         return float(result[0]) if result else 0.0
    
# def create_sales_record(store_id, user_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             INSERT INTO Sales (store_id, user_id, insert_date)
#             VALUES (%s, %s, GETDATE())
#             OUTPUT INSERTED.sales_id
#         """, [store_id, user_id])
#         result = cursor.fetchone()
#         return result[0] if result else None    
# # Helper function to check stock
# def check_stock(product_id, store_id, counter_id, quantity):
#     product_amount = get_total_product_amount(product_id, store_id, counter_id)
#     if product_amount and product_amount["amount"] >= quantity:
#         return True
#     return False

# # Helper function to deduct stock
# def deduct_stock_from_all_counters(product_id, store_id, quantity):
#     if quantity <= 0:
#         raise ValueError("Quantity must be a positive integer")

#     with connection.cursor() as cursor:
#         cursor.execute("""
#             UPDATE Product_Amount
#             SET amount = CASE
#                 WHEN amount >= %s THEN amount - %s
#                 ELSE 0
#             END
#             OUTPUT INSERTED.counter_id, INSERTED.amount
#             WHERE product_id = %s AND store_id = %s AND amount > 0
#         """, [quantity, quantity, product_id, store_id])

#         # Check if the deduction was successful
#         updated_rows = cursor.fetchall()
#         total_deducted = sum(row[1] for row in updated_rows)

#         if total_deducted < quantity:
#             raise ValueError("Insufficient stock for product ID: {}".format(product_id))

#         # Return the counter_id from the first updated row
#         if updated_rows:
#             return updated_rows[0][0]  # Return the counter_id
#         else:
#             raise ValueError("No counters updated for product ID: {}".format(product_id))

# # Helper function to calculate the next details_id
# def get_next_details_id(sales_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             SELECT ISNULL(MAX(details_id), 0) + 1
#             FROM Sales_details
#             WHERE sales_id = %s
#         """, [sales_id])
#         result = cursor.fetchone()
#         return result[0] if result else 1

# def create_sales_detail(sales_id, product_id, counter_id, quantity, sell_price, buy_price):
#     # Ensure counter_id is not None
#     if counter_id is None:
#         raise ValueError("Counter ID cannot be None")
#     # Calculate the next details_id
#     details_id = get_next_details_id(sales_id)

#     with connection.cursor() as cursor:
#         cursor.execute("""
#             INSERT INTO Sales_details (
#                 details_id, sales_id, product_id, counter_id, amount, sale_unit_change, sale_unit, 
#                 sell_price, buy_price, disc_money, disc_per, total_sell, back, back_amount, 
#                 back_unit, back_gf_id, insert_uid, insert_date
#             ) VALUES (
#                 %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE()
#             )
#         """, [
#             details_id, sales_id, product_id, counter_id, quantity, 1.0, 1,
#             float(sell_price), float(buy_price), 0.0, 0.0, float(sell_price) * quantity, "N", 0.0, 0, None, "API_USER"
#         ])

#         if cursor.rowcount == 0:
#             raise ValueError("Failed to create sale detail")

# def get_all_counter_stock(product_id, store_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             SELECT counter_id, amount
#             FROM Product_Amount
#             WHERE product_id = %s AND store_id = %s AND amount > 0
#         """, [product_id, store_id])

#         results = cursor.fetchall()
#         if results:
#             # Return a dictionary with counter_id as key and amount as value
#             return {str(row[0]): int(row[1]) for row in results}
#         return {}



query_head = """
           SELECT 
                p.product_id,
                p.product_code,
                p.product_name_ar,
                p.product_name_en,
                (
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit1
				)as product_unit1,
                p.sell_price,

				(
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit2
				)as product_unit2,
				p.product_unit1_2,
				p.unit2_sell_price,
				(
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit3
				)as product_unit3,
				p.product_unit1_3,
				p.unit3_sell_price,
                ISNULL((
                    SELECT CAST(SUM(pa.amount) AS INT) 
                    FROM Product_Amount pa 
                    WHERE pa.product_id = p.product_id
                ), 0) AS amount,
                p.product_image_url,
                (
                select pd.pd_name_ar
                from Product_description pd
                where pd.pd_id=p.pd_id
                )as product_description,
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
                )) AS product_group,
                (
                    SELECT STRING_AGG(pi.image_url, ', ') -- Concatenate image URLs into a single string
                    FROM Product_Images pi
                    WHERE pi.product_id = p.product_id
                ) AS product_images -- Returns all image URLs as a comma-separated string
                

            FROM Products p
            -- Join with product_group to access category_id
			JOIN product_groups pg ON p.group_id = pg.group_id
                """
