import java.io.IOException;
import java.io.BufferedReader;
import java.io.PrintWriter;
import java.util.Base64;
import java.util.Enumeration;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
public class Server extends HttpServlet {
    private static final long serialVersionUID = 1L;
    public void doAnything(HttpServletRequest request,
        HttpServletResponse response, String method)
    throws IOException, ServletException {
        response.setContentType("text/json");
        response.setCharacterEncoding("UTF-8");
        PrintWriter out = response.getWriter();
        out.print("{\"headers\":[");
        Enumeration e = request.getHeaderNames();
        Boolean first = true;
        while (e.hasMoreElements()) {
            String headerName = (String) e.nextElement();
            String headerValue = request.getHeader(headerName);
            if (!first) {
                out.print(",");
            } else {
                first = false;
            }
            out.print("[\"" + Base64.getEncoder().encodeToString(headerName.getBytes("utf-8")) + "\",");
            out.print("\"" + Base64.getEncoder().encodeToString(headerValue.getBytes("utf-8")) + "\"]");
        }
        out.print("],\"uri\":\"" + Base64.getEncoder().encodeToString((request.getPathInfo() + (request.getQueryString() != null ? ("?" + request.getQueryString()) : "")).getBytes("utf-8")) + "\",");
        out.print("\"method\":\"" + Base64.getEncoder().encodeToString(method.getBytes("utf-8")) + "\",");
        out.print("\"version\":\"" + Base64.getEncoder().encodeToString(request.getProtocol().getBytes("utf-8")) + "\",");
        out.print("\"body\":\"" + Base64.getEncoder().encodeToString(request.getInputStream().readAllBytes()) + "\"}");
    }
    @Override
    public void doGet(HttpServletRequest request,
        HttpServletResponse response)
    throws IOException, ServletException {
        doAnything(request, response, "GET");
    }
    @Override
    public void doPost(HttpServletRequest request,
        HttpServletResponse response)
    throws IOException, ServletException {
        doAnything(request, response, "POST");
    }
    @Override
    public void doHead(HttpServletRequest request,
        HttpServletResponse response)
    throws IOException, ServletException {
        doAnything(request, response, "HEAD");
    }
    @Override
    public void doDelete(HttpServletRequest request,
        HttpServletResponse response)
    throws IOException, ServletException {
        doAnything(request, response, "DELETE");
    }
    @Override
    public void doPut(HttpServletRequest request,
        HttpServletResponse response)
    throws IOException, ServletException {
        doAnything(request, response, "PUT");
    }
    @Override
    public void doOptions(HttpServletRequest request,
        HttpServletResponse response)
    throws IOException, ServletException {
        doAnything(request, response, "OPTIONS");
    }
    @Override
    public void doTrace(HttpServletRequest request,
        HttpServletResponse response)
    throws IOException, ServletException {
        doAnything(request, response, "TRACE");
    }
}
