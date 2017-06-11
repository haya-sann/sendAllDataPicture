#!/bin/bash
#
#
#!/bin/bash
#

echo -e "\e[42;31mモデムの状態をテスト\e[m"

[ -e /sys/class/net/ppp0/carrier ] && echo PPP is on || echo PPP is off

exit 0
