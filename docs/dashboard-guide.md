# Dashboard Guide 

## Web Tier Health Dashoard

This section displays the general information about the server health. The indicators give an overview about the web server status. 

1. **Current Request Rate:** This widget shows the metric that represents the number of requests received by the server per minute. 
2. **Error Rate (%):** This widget shows the calculation of the error responses in relationship with the total requests. 
3. **P95 Latency (ms):** This widget shows the response time of the targets for 95% of the requests. Percentile 95 is used to show the real user experience. 
4. **Healthy Targets:** This widget displays the total amount of targets that are healthy for the Application Load Balancer 

![Web Tier Health Dashoard](../presentation/screenshots/01-health-dashboard.png)

---

## Golden Signals

This section displays the golden signals of the server, which are the basic signals to monitor in order to ensure that the server is working properly. 

1. **Traffic - Request Rate:** This widget contains a line graph that displays the request count history along time. 
2. **Errors - HTTP Status Codes:** This widget contains a line graph that displays the count of the different HTTP Status Code Responses, which are filtered by HTTP Code 2XX, HTTP Code 4XX and HTTP Code 5XX. 
3. **Latency - Response Time Percentiles:** This widget contains a line graph with the percentiles P50, P95 and P99 of the response time. This helps to compare the response time for each request. 
4. **Saturation - Target Health:** This widgets contains a line graph with the count of healthy and unhealthy targets along time. 

![Golden Signals](../presentation/screenshots/02-golden-signals.png)

---

## EC2 Resource Utilization

This section shows information about the instance behavior. 

1. **CPU Utilization:** This widget shows the percentage of CPU Usage along time. As annotation, a warning line is placed at 70% to improve the visualization of a potential issue related to CPU Usage. 
2. **Memory Utilization:** This widget shows how much memory has been used in the instance. 
3. **Network In/Out:** This widget contains a line graph that indicate the amount of data that is inbounded and outbounded from the server. 
4. **Disk Usage:** This widget shows how much disk space has been used in the instance.

![EC2 Resource Utilization](../presentation/screenshots/03-ec2-utilization.png)

---

## Correlation View 

This graphic combines the data of the following metrics along time: 

- P95 Latency
- Request Rate 
- HTTP 5XX Code Responses
- CPU Usage

The purpose of this combination is to facilitate the Root Cause Analisys by comparing the behavior of these metrics in a specific point in time. 

![Correlation View](../presentation/screenshots/04-correlation-view.png)

## Order Service

This section contains information related to the bussiness, i. e., the history about the user experience with the web server. 

1. **Complete Carts:** This widgets shows the total amount of carts that were completed (purchase closed).
2. **Abandoned Carts:** This widget shows the total amount of abandoned carts, i. e., carts that were created but not completed. 
3. **Total Carts:** This widget shows the total amount of carts: carts completed, carts abandoned and carts active (carts that were created but they are neither closed nor abandoned)
4. **CartAbandonmentRate:** This widgets contains a line graph that shows the percentage of abandoned carts compare to the total carts along time.

![Order Service](../presentation/screenshots/05-order-service.png)