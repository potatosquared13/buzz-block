package com.example.buzzbraceletadmin;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.FileNotFoundException;

import java.io.InputStream;
import java.io.OutputStream;
import java.math.BigInteger;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.DatagramPacket;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.MulticastSocket;
import java.net.SocketException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Formatter;
import java.util.Locale;
import java.util.Set;
import java.util.HashSet;
import java.util.Scanner;
import java.util.ArrayList;

import android.content.Context;
import android.net.wifi.WifiManager;
import android.os.AsyncTask;
import android.os.Environment;
import android.util.Base64;
import java.util.Collections;
import java.util.zip.DataFormatException;
import java.util.zip.Deflater;
import java.util.zip.DeflaterOutputStream;
import java.util.zip.Inflater;
import java.util.zip.InflaterInputStream;
import java.security.Signature;
import java.security.PublicKey;
import java.security.KeyFactory;
import java.security.spec.X509EncodedKeySpec;

import static android.content.ContentValues.TAG;
import static android.content.Context.WIFI_SERVICE;

public class Node extends AsyncTask<Void, Void, Void>{
    private static final int RESPONSE = 0;
    private static final int TRANSACTION = 1;
    private static final int BFTSTART = 2;
    private static final int BFTVERIFY = 3;
    private static final int BALANCEREQUEST = 4;
    private static final int BALANCE = 5;
    private static final int CHAINREQUEST = 6;
    private static final int CHAIN = 7;
    private static final int PEER = 8;
    private static final int LEADER = 9;
    private static final int UNKNOWN = 10;

    protected Void doInBackground(Void... arg0) {
        System.out.println("Starting node");
        start();
        try {
            while (control.leader == null) {
                Thread.sleep(4000);
            }
            if (control.chain.blocks.size() == 0) {
                System.out.println(control.leader.ip + ":" + control.leader.port);
                updateChain(control.leader.socket);
            }
            while (control.active)
                Thread.sleep(1000);
            stop();
        } catch (Exception e){
            e.printStackTrace();
        }
        return null;
    }

    private class Peer {
        Socket socket;
        String ip;
        int port;
        String identity;
        Peer(Socket s, String i, int p, String id){
            socket = s;
            ip = i;
            port = p;
            identity = id;
        }
    }

    private class IdentityHashPair {
        String identity;
        String hash;
        IdentityHashPair(String i, String h){
            identity = i;
            hash = h;
        }
    }

    private Context mContext;
    public class Control {
        volatile Boolean active;
        volatile String ip;
        volatile int port;
        volatile Set<Peer> peers;
        volatile ArrayList<Transaction> pending_transactions;
        volatile Block pending_block;
        volatile Blockchain chain;
        volatile ArrayList<IdentityHashPair> hashes;
        volatile Client client;
        volatile Peer leader;
        volatile ArrayList<String> blacklist;
    }
    public final Control control = new Control();

    private class UDPListener implements Runnable {
        boolean isActive = false;
        private Thread t;
        @Override
        public void run() { // listen
            try {
                while (control.active && control.ip == null)
                    Thread.sleep(1000);
                byte[] buf = new byte[256];
                MulticastSocket ms = new MulticastSocket(60000);
                InetAddress group = InetAddress.getByName("224.98.117.122");
                ms.joinGroup(group);
                isActive = true;
                System.out.println("Listening for broadcasts");
                while (control.active && isActive) {
                    DatagramPacket dp = new DatagramPacket(buf, buf.length);
                    ms.receive(dp);
                    String msg = new String(dp.getData());
                    String ip = ((InetSocketAddress)dp.getSocketAddress()).getAddress().getHostAddress();
                    if (msg.startsWith("62757a7aGP")){
                        int port = Integer.parseInt(msg.substring(10).replaceAll("[^\\d]", ""));
                        if (!ip.equals(control.ip) || port != control.port) {
                            while (!tcp.isActive)
                                Thread.sleep(1000);
                            tcp.connect(ip, port);
                        }
                    }
                }
            } catch (Exception e){
                e.printStackTrace();
            }
        }
        void start() {
            if (t == null)
                t = new Thread(this);
            t.start();
        }
    }

    private class TCPListener implements Runnable {
        boolean isActive = false;
        private Thread t;
        TCPListener(){
            int iip = ((WifiManager) mContext.getApplicationContext().getSystemService(WIFI_SERVICE)).getConnectionInfo().getIpAddress();
            iip = (ByteOrder.nativeOrder().equals(ByteOrder.LITTLE_ENDIAN)) ? Integer.reverseBytes(iip) : iip;
            byte[] ip = BigInteger.valueOf(iip).toByteArray();
            try {
                InetAddress addr = InetAddress.getByAddress(ip);
                control.ip = addr.getHostAddress();
            } catch (UnknownHostException e) {
                e.printStackTrace();
            }

        }
        @Override
        public void run() { // acceptConnections
            ServerSocket sock;
            Socket c;
            try {
                sock = new ServerSocket(62757, 8, Inet4Address.getByName(control.ip));
                while (control.port == 0) {
                    control.port = sock.getLocalPort();
                    Thread.sleep(1000);
                }
                sock.setSoTimeout(4000);
                isActive = true;
                System.out.println("Listening for connections");
                while (control.active && isActive) {
                    byte[] buf = new byte[96];
                    c = sock.accept();
                    InputStream is = c.getInputStream();
                    is.read(buf, 0, 96);
                    String id = Helper.bytesToHex(buf);
                    boolean newPeer = true;
                    for (Peer p : control.peers)
                        if (p.identity.equals(id)) {
                            newPeer = false;
                            break;
                        }
                    if (newPeer) {
                        Peer peer = new Peer(c, c.getInetAddress().getHostAddress(), c.getPort(), id);
                        OutputStream os = c.getOutputStream();
                        os.write(Helper.hexToBytes(control.client.getIdentity()));
                        os.flush();
                        control.peers.add(peer);
                        new Thread(new ManageConnection(peer)).start();
                    } else {
                        c.shutdownOutput();
                        c.shutdownInput();
                        c.close();
                    }
                }
            } catch (SocketTimeoutException e) {
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        void start() {
            if (t == null)
                t = new Thread(this);
            t.start();
        }
        void connect(String i, int p) throws Exception{
            if (!control.ip.equals(i) && control.port != p){
                boolean newPeer = true;
                for (Peer peer : control.peers)
                    if (peer.ip.equals(i) && peer.port == p) {
                        newPeer = false;
                        break;
                    }
                if (newPeer) {
                    try {
                        System.out.println("Connecting to "+i+":"+p);
                        Socket sock = new Socket(i, p);
                        sock.setSoTimeout(4000);
                        OutputStream os = sock.getOutputStream();
                        os.write(Helper.hexToBytes(control.client.getIdentity()));
                        os.flush();
                        byte[] buf = new byte[96];
                        InputStream is = sock.getInputStream();
                        is.read(buf, 0, 96);
                        String id = Helper.bytesToHex(buf);
                        Peer peer = new Peer(sock, i, p, id);
                        control.peers.add(peer);
                        new Thread(new ManageConnection(peer)).start();
                    } catch (SocketTimeoutException e){
                    }
                }
            }
        }
    }

    private class ManageConnection implements Runnable {
        private Peer peer;
        ManageConnection(Peer p) {
            peer = p;
        }
        @Override
        public void run() { // handleConnection
            System.out.println("Opened connection to "+peer.identity.substring(0,8)+"("+peer.ip+":"+peer.port+")");
            try {
                peer.socket.setSoTimeout(4000);
            } catch (Exception e) {
                e.printStackTrace();
            }
            while (control.active && tcp.isActive && !peer.socket.isClosed()){
                try {
                    Message m = receive(peer);
                    if (m.data.isEmpty())
                        break;
                    switch (m.type) {
                        case RESPONSE:
                            System.out.println("Response from " + peer.identity.substring(0,8) + ": " + m.data
                            );
                            break;
                        case TRANSACTION:
                            System.out.println("Transaction from " + peer.identity.substring(0,8));
                            Transaction t = Transaction.fromJson(m.data);
                            if (!recordTransaction(t, peer.identity))
                                send(peer.socket, RESPONSE, "Invalid transaction");
                            break;
                        case BFTSTART:
                            System.out.println("Verifying new block");
                            ArrayList<Transaction> ts = new Gson().fromJson(m.data, new TypeToken<ArrayList<Transaction>>() {
                            }.getType());
                            sendHash(ts);
                            break;
                        case BFTVERIFY:
                            System.out.println("Hash from "+peer.identity.substring(0,8));
                            IdentityHashPair h = new IdentityHashPair(peer.identity, m.data);
                            control.hashes.add(h);
                            break;
                        case CHAINREQUEST:
                            System.out.println("Sending blockchain to "+peer.identity.substring(0,8));
                            while (control.active && control.pending_block != null)
                                Thread.sleep(2000);
                            if (!m.data.equals(control.chain.getHash()))
                                send(peer.socket, CHAIN, control.chain.toJson());
                            break;
                        case CHAIN:
                            if (!m.data.equals("UP TO DATE")) {
                                System.out.println("Chain is now up to date");
                                control.chain.rebuild(m.data);
                            } else System.out.println("Chain is already up to date");
                            break;
                        case LEADER:
                            System.out.println("Found leader node at "+peer.ip+":"+peer.port);
                            control.leader = peer;
                            break;
                        default:
                            System.out.println("Unknown message (" + m.type + ", " + m.data + ")");
                    }
                } catch (SocketTimeoutException e) {
                    continue;
                } catch (SocketException e){
                    break;
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
            try {
                System.out.println("Peer "+peer.identity.substring(0,8)+" disconnected");
                peer.socket.close();
                control.peers.remove(peer);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }


    private class ConsensusHandler implements Runnable {
        @Override
        public void run() { // pbft
            long start = System.nanoTime();
            while (System.nanoTime() - start < 60E9 && control.hashes.size() <= control.peers.size())
                try{
                    Thread.sleep(2000);
                } catch (InterruptedException e){
                    e.printStackTrace();
                }
            ArrayList<String> hashes = new ArrayList<String>();
            for (int i = 0; i < control.hashes.size(); i++)
                hashes.add(control.hashes.get(i).hash);
            if (hashes.size() < control.peers.size() + 1)
                for (int i = 0 ; i < (1 + control.hashes.size() - hashes.size()) ; i++)
                    hashes.add("0");
            int  maxCount=0;
            String mode = null;
            String[] ha = hashes.toArray(new String[0]);
            for (int i = 0; i < hashes.size(); ++i) {
                int count = 0;
                for (int j = 0; j < hashes.size(); ++j)
                    if (ha[j].equals(ha[i]))
                        count++;
                if (count > maxCount) {
                    maxCount = count;
                    mode = ha[i];
                }
            }
            if (Collections.frequency(hashes, mode) >= 2/3 && control.pending_block.getHash().equals(mode)){
                System.out.println("Own hash matches network majority");
                control.chain.newBlock(control.pending_block);
                control.chain.export();
            } else {
                try {
                    updateChain(control.leader.socket);
                } catch (Exception e){
                    e.printStackTrace();
                }
            }
            control.hashes = new ArrayList<IdentityHashPair>();
            control.pending_block = null;
        }
    }

    private TCPListener tcp;
    private UDPListener udp;

    Node(File clientFile, Context c) {
        mContext = c;
        control.client = new Client(clientFile);
        control.active = false;
        control.ip = null;
        control.port = 0;
        control.peers = new HashSet<>();
        control.leader = null;
        control.pending_block = null;
        control.pending_transactions = new ArrayList<Transaction>();
        control.hashes = new ArrayList<IdentityHashPair>();
        control.chain = new Blockchain();
        File f = new File(Environment.getExternalStorageDirectory().getAbsolutePath() + "blockchain.json");
        if (f.exists() && !f.isDirectory()){
            try{
                Scanner s = new Scanner(f);
                s.useDelimiter("\\Z");
                control.chain.rebuild(s.next());
                s.close();
            } catch (FileNotFoundException e){
                e.printStackTrace();
            }
        }
        tcp = new TCPListener();
        udp = new UDPListener();
    }
    private void start() {
        if (!control.active){
            tcp.start();
            udp.start();
            control.active = true;
        }
    }
    public void stop() {
        if (control.active)
            control.active = false;
            tcp.isActive = false;
            udp.isActive = false;
            for (Peer p : control.peers)
                if (!p.socket.isClosed()) {
                    try {
                        p.socket.shutdownInput();
                        p.socket.shutdownOutput();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
    }
    private void send(final Socket s, final int t, final String m) {
        new Thread((new Runnable(){
            public void run(){
                try {
                    // compress message
                    byte[] input = m.getBytes();
                    ByteArrayOutputStream baos = new ByteArrayOutputStream();
                    DeflaterOutputStream od = new DeflaterOutputStream(baos, new Deflater(9));
                    for (byte b : input)
                        od.write(b);
                    od.close();

                    // encode to base64
                    byte[] payload = android.util.Base64.encode(baos.toByteArray(), Base64.DEFAULT);

                    // send data to peer (data = LLLLLLLLLLTTN... where T = message type, L = message length, N... = compressed message encoded in base64)
                    DataOutputStream dos = new DataOutputStream(s.getOutputStream());
                    dos.write(String.format(Locale.getDefault(), "%08X", payload.length).getBytes());
                    dos.write(String.format(Locale.getDefault(), "%02X", t).getBytes());
                    dos.write(payload);
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        })).start();
    }
    private Message receive(Peer p) throws IOException {
        DataInputStream input = new DataInputStream(p.socket.getInputStream());

        // read message length
        byte[] blength = new byte[8];
        int length;
        try {
            input.read(blength, 0, 8);
            length = Integer.parseInt(new String(blength), 16);
        } catch (NumberFormatException e){
            return new Message(0, "");
        }

        // read message type
        byte[] btype = new byte[2];
        input.read(btype, 0, 2);
        int type = Integer.parseInt(new String(btype), 16);

        //read message
        byte[] ecdata = new byte[length];
        input.readFully(ecdata, 0, length);

        // decode from base64
        byte[] compressed_data = android.util.Base64.decode(ecdata, Base64.DEFAULT);

        // decompress
        InflaterInputStream iis = new InflaterInputStream(new ByteArrayInputStream(compressed_data));
        ByteArrayOutputStream baos = new ByteArrayOutputStream(compressed_data.length);
        int b;
        while ((b = iis.read()) != -1){
            baos.write(b);
        }
        String msg = new String(baos.toByteArray());
        return new Message(type, msg);
    }
    private void getPeers() throws Exception {
        while (control.ip == null || control.port == 0)
            Thread.sleep(1000);
        byte[] msg = ("62757a7aGP" + control.port).getBytes();
        MulticastSocket ms = new MulticastSocket();
        InetAddress group = InetAddress.getByName("224.98.117.122");
        DatagramPacket dp = new DatagramPacket(msg, msg.length, group, 60000);
        System.out.println("Sending broadcast message ("+new String(msg)+")");
        ms.send(dp);
        ms.close();
    }
    public void sendPayment(String i, double a) {
        sendTransaction(1, i, a);
    }
    public void sendTransaction(int t, String i, double a) {
        while (control.active && control.pending_block != null)
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e){
                e.printStackTrace();
            }
        Transaction txn = null;
        if (t == 1)
            txn = new Transaction(1, i, control.client.getIdentity(), a);
        else {
            System.out.println("Invalid transaction type");
            return;
        }
        control.client.sign(txn);
        control.pending_transactions.add(txn);
        System.out.println(txn.toJson());
        for (Peer p : control.peers) {
            send(p.socket, TRANSACTION, txn.toJson());
        }
    }
    public double getBalance(String i){
        double balance = 0;
        for (Block b : control.chain.blocks){
            for (Transaction t : b.transactions){
                if (t.address.startsWith(i) && (t.transaction == 0 || t.transaction == 2)){
                        balance += t.amount;
                } else if (t.transaction == 1 && t.sender.startsWith(i)){
                    balance -= t.amount;
                }
            }
        }
        for (Transaction t : control.pending_transactions){
            if (t.address.startsWith(i) && (t.transaction == 0 || t.transaction == 2)){
                balance += t.amount;
            } else if (t.transaction == 1 && t.sender.startsWith(i)){
                balance -= t.amount;
            }
        }
        return balance;
    }
    private boolean isValidSignature(Transaction t, String i) throws Exception {
        if (!t.signature.isEmpty()) {
            byte[] identity = Helper.hexToBytes("3076301006072a8648ce3d020106052b8104002203620004" + i);
            Signature sig = Signature.getInstance("SHA256withECDSA");
            PublicKey pk = KeyFactory.getInstance("EC").generatePublic(new X509EncodedKeySpec(identity));
            sig.initVerify(pk);
            sig.update(Helper.hexToBytes(t.getHash()));
            return sig.verify(Helper.hexToBytes(t.signature));
        }
        return false;
    }
    // TODO
    private boolean recordTransaction(Transaction t, String i) throws Exception {
        if (control.blacklist.contains(i))
            return false;
        if (t.sender != t.address && isValidSignature(t, i)){
            switch (t.transaction) {
            case 0: // initial balance

                break;
            case 1: // payment
                if (t.address == i && getBalance(t.sender) >= t.amount)
                    control.pending_transactions.add(t);
                break;
            case 2: // add funds
                if (t.sender == i && i == control.leader.identity)
                    control.pending_transactions.add(t);
                break;
            case 3: // disable wallet
                control.blacklist.add(t.sender);
                break;
            default:
                return false;
            }
            return true;
        }
        return false;
    }
    private void updateChain(Socket sock) throws Exception {
        System.out.println("Requesting up to date chain");
        send(sock, CHAINREQUEST, control.chain.getHash());
    }
    private void sendHash(ArrayList<Transaction> t) throws Exception {
        if (control.pending_block == null) {
            control.pending_block = new Block(control.chain.getLastBlock().getHash(), t);
            control.pending_transactions = new ArrayList<>();
            for (Peer p : control.peers)
                send(p.socket, BFTVERIFY, control.pending_block.getHash());
            control.hashes.add(new IdentityHashPair(control.client.getIdentity(), control.pending_block.getHash()));
            new Thread(new ConsensusHandler()).start();
        }
    }
}