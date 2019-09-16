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

import java.net.Socket;
import java.net.DatagramPacket;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.MulticastSocket;
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

public class Node {
    private static final int RESPONSE = 0;
    private static final int TRANSACTION = 1;
    private static final int BFTSTART = 2;
    private static final int BFTVERIFY = 3;
    // private static final int BALANCEREQUEST = 4;
    // private static final int BALANCE = 5;
    private static final int CHAINREQUEST = 6;
    private static final int CHAIN = 7;
    private static final int PEER = 8;
    private static final int LEADER = 9;
    // private static final int UNKNOWN = 10;

    private class Peer {
        String ip;
        int port;
        String identity;
        Peer(String i, int p, String id){
            ip = i;
            port = p;
            identity = id;
        }
    }

    private class PeerHashPair {
        Peer peer;
        String hash;
        PeerHashPair(Peer p, String h){
            peer = p;
            hash = h;
        }
    }

    public class Control{
        volatile Boolean listening;
        volatile String ip;
        volatile int port;
        volatile Set<Peer> peers;
        volatile ArrayList<Transaction> pending_transactions;
        volatile Block pending_block;
        volatile Blockchain chain;
        volatile ArrayList<PeerHashPair> hashes;
        volatile Client client;
        volatile Peer leader;
    }    
    public final Control control = new Control();

    private class TCPListener implements Runnable{
        boolean isActive = false;
        private Thread t;
        @Override
        public void run() {
            ServerSocket sock = null;
            Socket c = null;
            try {
                control.ip = Inet4Address.getLocalHost().getHostAddress();
                sock = new ServerSocket(0, 8, Inet4Address.getByName(control.ip));
                control.port = sock.getLocalPort();
                sock.setSoTimeout(4000);
                System.out.println("Listening on " + control.ip + ":" + control.port);
                isActive = true;
                while (control.listening){
                    try{
                        c = sock.accept();
                        new Thread(new ConnectionManager(c)).start();
                    } catch (SocketTimeoutException e) {
                        continue;
                    }
                }
                isActive = false;
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        void start(){
            if (t == null)
                t = new Thread(this);
            t.start();
        }
    }

    private class UDPListener implements Runnable{
        boolean isActive = false;
        private Thread t;
        @Override
        public void run() {
            try {
                byte[] buf = new byte[256];
                MulticastSocket ms = new MulticastSocket(60000);
                InetAddress group = InetAddress.getByName("224.98.117.122");
                ms.joinGroup(group);
                isActive = true;
                while (control.listening){
                    DatagramPacket dp = new DatagramPacket(buf, buf.length);
                    ms.receive(dp);
                    String msg = new String(dp.getData());
                    String ip = dp.getAddress().getHostAddress();
                    if (msg.startsWith("62757a7aGP")){
                        String[] p = msg.substring(10).split(",");
                        int port = Integer.parseInt(p[0]);
                        String identity = p[1];
                        if (!control.ip.equals(ip) && control.port != port){
                            boolean alreadyKnown = false;
                            synchronized (control){
                                for (Peer peer : control.peers)
                                    if (peer.identity.equals(identity)){
                                        alreadyKnown = true;
                                        break;
                                    }
                                if (!alreadyKnown)
                                    control.peers.add(new Peer(ip, port, identity)); 
                            }
                            Socket sock = new Socket(ip, port);
                            msg = control.port + "," + control.client.getIdentity();
                            send(sock, PEER, msg);
                            sock.close();
                        }
                    } else if (msg.startsWith("62757a7aDC")){
                        synchronized (control){
                            for (Peer peer : control.peers){
                                if (peer.ip.equals(ip) && peer.port == ms.getPort())
                                    control.peers.remove(peer);
                            }
                        }
                    }
                }
                ms.close();
                isActive = false;
            } catch (Exception e){
                e.printStackTrace();
            }
        }
        void start(){
            if (t == null)
                t = new Thread(this);
            t.start();
        }
    }

    private class ConnectionManager implements Runnable{
        private Socket sock;
        ConnectionManager(Socket c){
            sock = c;
        }    
        @Override
        public void run() {
            String address = sock.getInetAddress().getHostAddress();
            Message m = receive(sock);
            String[] p;
            int port;
            String identity;
            switch(m.type){
            case RESPONSE:
                System.out.println("Response from " + address + ": " + m.data);
                break;
            case TRANSACTION:
                System.out.println("Transaction from " + address);
                Transaction t = Transaction.fromJson(m.data);
                if (! recordTransaction(t))
                    send(sock, RESPONSE, "Invalid transaction");
                break;
            case BFTSTART:
                System.out.println("Validating new block");
                ArrayList<Transaction> transactions = new Gson().fromJson(m.data, new TypeToken<ArrayList<Transaction>>() {}.getType());
                sendHash(transactions);
                break;
            case BFTVERIFY:
                if (control.hashes.isEmpty())
                    try {
                        Thread.sleep(1000);
                    } catch (InterruptedException e){
                        e.printStackTrace();
                    }
                synchronized (control){
                    for (Peer peer : control.peers)
                        if (peer.ip.equals(address) && peer.port == sock.getPort())
                            control.hashes.add(new PeerHashPair(peer, m.data));
                }
                break;
            case CHAINREQUEST:
                while (control.pending_block != null)
                    try {
                        Thread.sleep(1000);
                    } catch (InterruptedException e){
                        e.printStackTrace();
                    }
                synchronized (control){
                    if (!m.data.equals(control.chain.getHash())){
                        System.out.println("Sending chain to " + address);
                        send(sock, CHAIN, control.chain.toJson());
                    }
                }
                break;
            case CHAIN:
                synchronized (control){
                    if (!m.data.equals("UP TO DATE")){
                        System.out.println("Rebuilding chain");
                        control.chain.rebuild(m.data);
                    } else
                        System.out.println("Chain is already up to date");
                }
                break;
            case PEER:
                p = m.data.split(",");
                port = Integer.parseInt(p[0]);
                identity = p[1];
                boolean alreadyKnown = false;
                synchronized (control){
                    for (Peer peer : control.peers){
                        if (peer.identity.equals(identity)){
                            alreadyKnown = true;
                            break;
                        }
                    }
                    if (!alreadyKnown){
                        control.peers.add(new Peer(address, port, identity));
                        System.out.println("New peer at " + address + ":" + port);
                    }
                }
                break;
            case LEADER:
                p = m.data.split(",");
                port = Integer.parseInt(p[0]);
                identity = p[1];
                control.leader = new Peer(address, port, identity);
                System.out.println("Leader discovered at " + address + ":" + port);
                break;
            default:
                System.out.println("Unknown message (" + m.type + ", " + m.data + ")");
            }
            try {
                sock.close();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    private TCPListener tcp;
    private UDPListener udp;

    public Node(File clientFile) {
        control.listening = false;
        control.peers = new HashSet<>();
        control.pending_block = null;
        control.pending_transactions = new ArrayList<Transaction>();
        control.hashes = new ArrayList<PeerHashPair>();
        control.chain = new Blockchain();
        File f = new File("blockchain.json");
        if (f.exists() && !f.isDirectory()) {
            try {
                Scanner s = new Scanner(f);
                s.useDelimiter("\\Z");
                control.chain.rebuild(s.next());
                s.close();
            } catch (FileNotFoundException e) {
                e.printStackTrace();
            }
        }
        control.client = new Client(clientFile);
    }

    public void start() throws InterruptedException, IOException {
        if (!control.listening){
            control.listening = true;
            if (tcp == null)
                tcp = new TCPListener();
            if (udp == null)
                udp = new UDPListener();
            tcp.start();
            udp.start();
            while (! tcp.isActive && ! udp.isActive)
                Thread.sleep(1000);
            getLeader();
            getPeers();
        }
    }

    public void stop()throws InterruptedException, IOException{
        if (control.listening){
            control.listening = false;
            control.chain.export();
            disconnect();
        }
    }

    public void sendTransaction(String sender, double amount) {
        Transaction t = new Transaction(sender, control.client.getIdentity(), amount);
        control.client.sign(t);
        synchronized (control){
            control.pending_transactions.add(t);
        }
        synchronized (control){
            for (Peer p : control.peers){
                try{
                    Socket sock = new Socket(p.ip, p.port);
                    send(sock, TRANSACTION, t.toJson());
                    sock.close();
                } catch (UnknownHostException e){
                    e.printStackTrace();
                } catch (IOException e){
                    System.out.println("Connection refused (" + p.ip + ":" + p.port + ")");
                    e.printStackTrace();
                }
            }
        }
    }

    public double getBalance(String client){
        double balance = 0;
        synchronized (control){
            for (Block b : control.chain.blocks)
                for (Transaction t : b.transactions)
                    if (t.sender.equals(client))
                        balance -= t.amount;
                    else if (t.recipient.equals(client))
                        balance += t.amount;
            for (Transaction t : control.pending_transactions)
                if (t.sender.equals(client))
                    balance -= t.amount;
                else if (t.recipient.equals(client))
                    balance += t.amount;
        }
        return balance;
    }

    private Boolean isValidTransaction(Transaction t){
        byte[] identity;
        if (! t.signature.isEmpty()){
            if (t.sender.equals("add funds"))
                identity = Helper.hexToBytes("3076301006072a8648ce3d020106052b8104002203620004" + control.leader.identity);
            else
                identity = Helper.hexToBytes("3076301006072a8648ce3d020106052b8104002203620004" + t.recipient);
            try{
                Signature sig = Signature.getInstance("SHA256withECDSA");
                PublicKey pk = KeyFactory.getInstance("EC").generatePublic(new X509EncodedKeySpec(identity));
                sig.initVerify(pk);
                sig.update(Helper.hexToBytes(t.getHash()));
                return sig.verify(Helper.hexToBytes(t.signature));
            } catch (Exception e){
                e.printStackTrace();
            }
    }
        return false;
    }

    private Boolean recordTransaction(Transaction t){
        if (!t.sender.equals(t.recipient) && !t.recipient.equals(control.leader.identity) && this.isValidTransaction(t)){
            synchronized (control){
                control.pending_transactions.add(t);
            }
            return true;
        }
        return false;
    }

    private void updateChain(Peer p) throws IOException{
        Socket sock = new Socket(p.ip, p.port);
        synchronized (control){
            if (control.chain.blocks.size() == 0)
                send(sock, CHAINREQUEST, "0");
            else
                send(sock, CHAINREQUEST, control.chain.getHash());
        }
        sock.close();
    }

    private void getPeers() throws InterruptedException, IOException {
        while (control.ip == null)
            Thread.sleep(1000);
        byte[] msg = ("62757a7aGP" + control.port + "," + control.client.getIdentity()).getBytes();
        MulticastSocket ms = new MulticastSocket();
        InetAddress group = InetAddress.getByName("224.98.117.122");
        DatagramPacket dp = new DatagramPacket(msg, msg.length, group, 60000);
        ms.send(dp);
        ms.close();
    }

    private void getLeader() throws IOException {
        control.leader = null;
        byte[] msg = ("62757a7aCN" + control.port).getBytes();
        MulticastSocket ms = new MulticastSocket();
        InetAddress group = InetAddress.getByName("224.98.117.122");
        DatagramPacket dp = new DatagramPacket(msg, msg.length, group, 60000);
        ms.send(dp);
        ms.close();
    }

    private void disconnect() throws IOException{
        byte[] msg = "62757a7aDC".getBytes();
        MulticastSocket ms = new MulticastSocket();
        InetAddress group = InetAddress.getByName("224.98.117.122");
        DatagramPacket dp = new DatagramPacket(msg, msg.length, group, 60000);
        ms.send(dp);
        ms.close();
    }

    private void send(Socket s, int t, String m){
        // String addr = s.getInetAddress().getHostAddress();
        // int port = s.getPort();
        byte[] input = m.getBytes();
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        DeflaterOutputStream od = new DeflaterOutputStream(baos, new Deflater(9));
        try {
            od.write(input);
            od.flush();
            od.close();
//            byte[] payload = Base64.getEncoder().encode(baos.toByteArray());
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

    /*
        TODO:
            - Read Bytes
     */

    private Message receive(Socket s){
        try {
            DataInputStream input = new DataInputStream(s.getInputStream());
            byte[] btype = new byte[2];
            input.read(btype, 0, 2);
            int type = Integer.parseInt(new String(btype));
//            int type = Integer.parseInt(new String(input.read()));
            byte[] blength = new byte[8];
            input .read(blength, 2, 8);
            int length = Integer.parseInt(new String(blength));
//            int length = Integer.parseInt(new String(input.readNBytes(8)));

            byte[] ecdata =  new byte[length];
            input.readFully(ecdata, 10, length);
//            byte[] encoded_compressed_data = input.readNBytes(length);
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

    private void sendHash(ArrayList<Transaction> p){
        control.pending_block = new Block(control.chain.getLastBlock().getHash(), p);
        try{
            for (Peer peer : control.peers){
                Socket sock = new Socket(peer.ip, peer.port);
                send(sock, BFTVERIFY, control.pending_block.getHash());
            }
        } catch (IOException e){
            System.out.println("Peer refused connection");
        }
        synchronized (control){
            if (!control.hashes.isEmpty())
            control.hashes = new ArrayList<PeerHashPair>();
            control.hashes.add(new PeerHashPair(new Peer(control.ip, control.port, control.client.getIdentity()), control.pending_block.getHash()));
        }
        pbft();
    }
    
    private synchronized void pbft() {
        System.out.println("Started consensus");
        control.pending_transactions = new ArrayList<Transaction>();
        long start = System.nanoTime();
        System.out.println("Waiting for all hashes or elapsed time");
        while (System.nanoTime() - start > 60E9 || control.hashes.size() < control.peers.size() + 1)
            try{
                Thread.sleep(1000);
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
            for (PeerHashPair ph : control.hashes){
                if (ph.hash.equals(mode)){
                    try{
                        updateChain(ph.peer);
                        break;
                    } catch (IOException e){
                        continue;
                    }
                }
            }
        }
        control.hashes = new ArrayList<PeerHashPair>();
        control.pending_block = null;
    }
}