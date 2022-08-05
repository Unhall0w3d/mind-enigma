import re
from pyparsing import Word, alphas, Suppress, Combine, nums, string, alphanums, OneOrMore, White, punc8bit


class Parser(object):
    def __init__(self):
        ints = Word(nums)
        punc = "-_.;"
        # Timestamp
        month = Word(string.ascii_uppercase, string.ascii_lowercase, exact=3)
        day = ints
        hour = Combine(ints + ":" + ints + ":" + ints)
        exhour = Combine(ints + ":" + ints + ":" + ints + "." + ints)
        year = ints

        timestamp = month + day + hour
        extimestamp = month + day + year + exhour
        tzdata = Word(string.ascii_uppercase, exact=3)

        # Hostname
        hostname = Word(alphanums + "-_.")

        # Local Syslog
        local = Word(alphanums)

        # Priority
        priority = ints

        # Server Type
        srvtype = Combine(Word(string.ascii_lowercase, exact=3) + Suppress(":"))

        # Message Number
        msgnum = Combine(ints + Suppress(":"))

        # Separator
        separator = ":   "

        # Message Type
        msgtype = Word("%:-_" + alphanums)

        # Device Name
        devname = Suppress("%[") + Combine("DeviceName=" + Word(alphanums)) + Suppress("]")

        # Device IP
        devip = Suppress("[") + Combine("IPAddress=" + Word(nums + ".")) + Suppress("]")

        # Protocol
        protocol = Suppress("[") + Combine("Protocol=" + Word(alphas)) + Suppress("]")

        # Device Type
        devtype = Suppress("[") + Combine("DeviceType=" + ints) + Suppress("]")

        # Description
        descval = Combine(OneOrMore(Word(alphanums + punc) | White(' ', max=1) + ~White()))
        desc = Suppress("[") + Combine("Description=" + OneOrMore(descval)) + Suppress("]")

        # Reason Code
        reason = Suppress("[") + Combine("Reason=" + ints) + Suppress("]")

        # IP Attributes
        ipattrib = Suppress("[") + Combine("IPAddrAttributes=" + Word(nums + ".", asKeyword=True)) + Suppress("]")

        # Last Signal Received
        lastsig = Suppress("[") + Combine("LastSignalReceived=" + Word(alphanums, asKeyword=True)) + Suppress("]")

        # App ID
        # appid = Suppress("[") + "AppID=" + Word(printables + " ") + Suppress("]")
        appidval = Combine(OneOrMore(Word(alphas) | White(' ', max=1) + ~White()))
        appid = Suppress("[") + Combine("AppID=" + OneOrMore(appidval)) + Suppress("]")

        # Call State
        callstate = Suppress("[") + Combine("CallState=" + Word(alphanums + punc)) + Suppress("]")

        # Cluster ID
        cluster = Suppress("[") + Combine("ClusterID=" + Word(alphanums)) + Suppress("]")

        # Node ID
        node = Suppress("[") + Combine("NodeID=" + Word(alphanums)) + Suppress("]:")

        # Info Text
        infoval = Combine(OneOrMore(Word(alphas) | White(' ', max=1) + ~White()))
        info = OneOrMore(infoval)

        # Build Patterns

        self.__endpointall = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp +\
            tzdata + separator + msgtype + devname + devip + protocol + devtype + desc + reason \
            + ipattrib + lastsig + appid + cluster + node + info
        self.__endpointnodesc = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp + \
            tzdata + separator + msgtype + devname + devip + protocol + devtype + reason \
            + ipattrib + lastsig + appid + cluster + node + info
        self.__endpointnosigcall = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp + \
            tzdata + separator + msgtype + devname + devip + protocol + devtype + desc + reason \
            + ipattrib + appid + cluster + node + info
        self.__endpointnosigdesc = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp + \
            tzdata + separator + msgtype + devname + devip + protocol + devtype + reason \
            + ipattrib + appid + cluster + node + info
        self.__endpointnosig = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp + \
            tzdata + separator + msgtype + devname + devip + protocol + devtype + desc + reason \
            + ipattrib + callstate + appid + cluster + node + info

    def parse(self, line):
        sigkywd = "LastSignalReceived"
        searching = re.compile(r'{}'.format(sigkywd))
        dosearch = searching.search(line)
        if dosearch is None:
            descsigkywd = "Description"
            descsearching = re.compile(r'{}'.format(descsigkywd))
            descsearch = descsearching.search(line)
            if descsearch is None:
                parsed = self.__endpointnosigdesc.parseString(line)
                # print("nosig-nodesc")
                # print(parsed)
                payload = {"device": parsed[16], "ip": parsed[17], "description": parsed[20], "reason": parsed[21],
                        "node": parsed[26]}
                return payload
            elif descsearch is not None:
                callkywd = "CallState"
                callsearching = re.compile(r'{}'.format(callkywd))
                callsearch = callsearching.search(line)
                if callsearch is None:
                    parsed = self.__endpointnosigcall.parseString(line)
                    # print("nosig-yesdesc-nocallstate")
                    # print(parsed)
                    payload = {"device": parsed[16], "ip": parsed[17], "description": parsed[20], "reason": parsed[21],
                        "node": parsed[25]}
                    return payload
                if callsearch is not None:
                    parsed = self.__endpointnosig.parseString(line)
                    # print("nosig-yesdesc-yescallstate")
                    # print(parsed)
                    payload = {"device": parsed[16], "ip": parsed[17], "description": parsed[20], "callstate": parsed[23], "reason": parsed[21],
                        "node": parsed[25]}
                    return payload
        elif dosearch is not None:
            descsigkywd = "Description"
            descsearching = re.compile(r'{}'.format(descsigkywd))
            descsearch = descsearching.search(line)
            if descsearch is None:
                parsed = self.__endpointnodesc.parseString(line)
                # print("yessig-nodesc")
                # print(parsed)
                payload = {"device": parsed[16], "ip": parsed[17], "lastsignal": parsed[22], "reason": parsed[20],
                "node": parsed[25]}
                return payload
            elif descsearch is not None:
                parsed = self.__endpointall.parseString(line)
                # print("all")
                # print(parsed)
                payload = {"device": parsed[16], "ip": parsed[17], "description": parsed[20], "reason": parsed[21],
                    "node": parsed[26]}
                return payload


def main():
    parser = Parser()
    search = '-EndPointUnregistered'
    searchpattern = re.compile(r'{}'.format(search))
    with open("test.txt") as syslogfile:
        for line in syslogfile:
            searchresult = searchpattern.search(line)
            if searchresult is None:
                continue
            elif searchresult is not None:
                fields = parser.parse(line)
                print(fields)


if __name__ == "__main__":
    main()
    exit()
