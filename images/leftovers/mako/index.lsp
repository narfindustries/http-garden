<?lsp
for key,value in pairs(request:data()) do
    print(key);
end

print(
    "{\"method\":\"",
        request:method(),
    "\",\"uri\":\"",
        request:uri(),
    "\",\"headers\":["
)
first = true
for k,v in pairs(request:header()) do
    print((first and "" or ","), "[\"", k, "\",\"", v, "\"]")
    first = false
end
print("], \"data\":\"")
print("\"}")
?>
