package com.example.peng.nfcreadwrite;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import java.io.File;
import java.io.IOException;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.FileNotFoundException;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;
import java.net.DatagramPacket;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.MulticastSocket;
import java.net.SocketException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.util.Locale;
import java.util.Set;
import java.util.HashSet;
import java.util.Scanner;
import java.util.ArrayList;
import android.util.Base64;
import java.util.Collections;
import java.util.zip.Deflater;
import java.util.zip.DeflaterOutputStream;
import java.util.zip.Inflater;
import java.util.zip.InflaterInputStream;
import java.security.Signature;
import java.security.PublicKey;
import java.security.KeyFactory;
import java.security.spec.X509EncodedKeySpec;

public class Node{
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
    }
    public final Control control = new Control();

    private class UDPListener implements Runnable {
        boolean isActive = false;
        private Thread t;
        @Override
        public void run() { // listen
            try {
                while (control.active && control.ip.isEmpty())
                    Thread.sleep(1000);
                byte[] buf = new byte[1024];
                MulticastSocket ms = new MulticastSocket(60000);
                InetAddress group = InetAddress.getByName("224.98.117.122");
                ms.joinGroup(group);
                isActive = true;
                while (control.active && isActive) {
                    DatagramPacket dp = new DatagramPacket(buf, buf.length);
                    ms.receive(dp);
                    String msg = new String(dp.getData());
                    String ip = dp.getAddress().getHostAddress();
                    if (msg.startsWith("62757a7aGP")){
                        int port = Integer.parseInt(msg.substring(10));
                        if (!control.ip.equals(ip) && control.port != port)
                            tcp.connect(ip, port);
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
        @Override
        public void run() { // acceptConnections
            ServerSocket sock;
            Socket c;
            try {
                control.ip = Inet4Address.getLocalHost().getHostAddress();
                sock = new ServerSocket(0, 8, Inet4Address.getByName(control.ip));
                control.port = sock.getLocalPort();
                sock.setSoTimeout(4000);
                isActive = true;
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
        void connect(String i, int p) {
            if (!control.ip.equals(i) && control.port != p){
                boolean newPeer = true;
                for (Peer peer : control.peers)
                    if (peer.ip.equals(i) && peer.port == p) {
                        newPeer = false;
                        break;
                    }
                if (newPeer) {
                    try {
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
                        new Thread(new ManageConnection(peer)).start();
                    } catch (SocketTimeoutException e){
                    } catch (Exception e) {
                        e.printStackTrace();
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
            try {
                peer.socket.setSoTimeout(4000);
            } catch (Exception e) {
                e.printStackTrace();
            }
            while (control.active && tcp.isActive){
                try {
                    Message m = receive(peer.socket);
                    if (m == null)
                        break;
                    switch (m.type) {
                        case RESPONSE:
                            System.out.println("Response from " + peer.identity.substring(10) + ": " + m.data
                            );
                            break;
                        case TRANSACTION:
                            Transaction t = Transaction.fromJson(m.data);
                            if (!recordTransaction(t, peer.identity))
                                send(peer.socket, RESPONSE, "Invalid transaction");
                            break;
                        case BFTSTART:
                            ArrayList<Transaction> ts = new Gson().fromJson(m.data, new TypeToken<ArrayList<Transaction>>() {
                            }.getType());
                            sendHash(ts);
                            break;
                        case BFTVERIFY:
                            IdentityHashPair h = new IdentityHashPair(peer.identity, m.data);
                            control.hashes.add(h);
                            break;
                        case CHAINREQUEST:
                            while (control.active && control.pending_block != null)
                                Thread.sleep(2000);
                            if (!m.data.equals(control.chain.getHash()))
                                send(peer.socket, CHAIN, control.chain.toJson());
                            break;
                        case CHAIN:
                            if (!m.data.equals("UP TO DATE"))
                                control.chain.rebuild(m.data);
                            break;
                        case LEADER:
                            control.leader = peer;
                            break;
                        default:
                            System.out.println("Unknown message (" + m.type + ", " + m.data + ")");
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
            try {
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
                updateChain(control.leader.socket);
            }
            control.hashes = new ArrayList<IdentityHashPair>();
            control.pending_block = null;
        }
    }

    TCPListener tcp = new TCPListener();
    UDPListener udp = new UDPListener();

    public Node(File clientFile){
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
        File f = new File("blockchain.json");
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
    }
    public void start() {
        if (!control.active){
            control.active = true;
            if (tcp == null)
                tcp = new TCPListener();
            if (udp == null)
                udp = new UDPListener();
            tcp.start();
            udp.start();
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
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }
    }
    public void send(Socket s, int t, String m) {
        byte[] input = m.getBytes();
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        DeflaterOutputStream od = new DeflaterOutputStream(baos, new Deflater(9));
        try {
            od.write(input);
            od.flush();
            od.close();
            byte[] payload = android.util.Base64.encode(baos.toByteArray(), Base64.DEFAULT);
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            out.write(String.format(Locale.getDefault(), "%02d", t).getBytes());
            out.write(String.format(Locale.getDefault(), "%08d", payload.length).getBytes());
            out.write(payload);
            DataOutputStream output = new DataOutputStream(s.getOutputStream());
            output.write(out.toByteArray());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    public Message receive(Socket s) {
        try {
            DataInputStream input = new DataInputStream(s.getInputStream());
            byte[] blength = new byte[8];
            input .read(blength, 0, 8);
            int length = Integer.parseInt(new String(blength));
            byte[] btype = new byte[2];
            input.read(btype, 2, 2);
            int type = Integer.parseInt(new String(btype));

            byte[] ecdata =  new byte[length];
            input.readFully(ecdata, 10, length);
            byte[] compressed_data = android.util.Base64.decode(ecdata, Base64.DEFAULT);
            InflaterInputStream iis = new InflaterInputStream(new ByteArrayInputStream(compressed_data), new Inflater());
            s.close();
            byte[] msg = new byte[length];
            iis.read(msg, 0, length);
            return new Message(type, new String(msg));
        } catch (IOException e){
            e.printStackTrace();
        }
        return null;
    }
    public void getPeers() {
        try {
            while (control.ip == null)
                Thread.sleep(1000);
            byte[] msg = ("62757a7aGP" + control.port + "," + control.client.getIdentity()).getBytes();
            MulticastSocket ms = new MulticastSocket();
            InetAddress group = InetAddress.getByName("224.98.117.122");
            DatagramPacket dp = new DatagramPacket(msg, msg.length, group, 60000);
            ms.send(dp);
            ms.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    public void sendTransaction(int t, String i, double a) {
        while (control.active && control.pending_block != null)
            try {
                Thread.sleep(1000);
            } catch (Exception e) {
                e.printStackTrace();
            }
        Transaction txn = null;
        if (t == 1)
            txn = new Transaction(1, i, control.client.getIdentity(), a);
        else if (t == 2)
            txn = new Transaction(2, control.client.getIdentity(), i, a);
        control.client.sign(txn);
        control.pending_transactions.add(txn);
        for (Peer p : control.peers)
            send(p.socket, TRANSACTION, txn.toJson());
    }
    public double getBalance(String i){
        double balance = 0;
        for (Block b : control.chain.blocks)
            for (Transaction t : b.transactions)
                if (t.sender.equals(i))
                    balance -= t.amount;
                else if (t.address.equals(i) && t.type == 2)
                    balance += t.amount;
         for (Transaction t : control.pending_transactions)
             if (t.sender.equals(i))
                 balance -= t.amount;
             else if (t.address.equals(i) && t.type == 2)
                 balance += t.amount;
        return balance;
    }
    private boolean isValidTransaction(Transaction t, String i) {
        if (!t.signature.isEmpty()) {
            try {
                byte[] identity = Helper.hexToBytes("3076301006072a8648ce3d020106052b8104002203620004" + i);
                Signature sig = Signature.getInstance("SHA256withECDSA");
                PublicKey pk = KeyFactory.getInstance("EC").generatePublic(new X509EncodedKeySpec(identity));
                sig.initVerify(pk);
                sig.update(Helper.hexToBytes(t.getHash()));
                return sig.verify(Helper.hexToBytes(t.signature));
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        return false;
    }
    private boolean recordTransaction(Transaction t, String i) {
        if (t.sender != t.address && isValidTransaction(t, i)) {
            control.pending_transactions.add(t);
            return true;
        }
        return false;
    }
    private void updateChain(Socket sock) {
        send(sock, CHAINREQUEST, control.chain.getHash());
    }
    private void sendHash(ArrayList<Transaction> t) {
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