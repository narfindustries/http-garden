unitd --no-daemon 2>/dev/null &

sleep 10

curl -X PUT --data-binary '{
  "listeners": {
      "*:80": {
          "pass": "applications/python"
      }
  },
  "applications": {
      "python": {
          "type": "python",
          "path": "/www/",
          "module": "wsgi"
      }
  }
}' --unix-socket /usr/local/var/run/unit/control.unit.sock http://localhost/config/


fg
